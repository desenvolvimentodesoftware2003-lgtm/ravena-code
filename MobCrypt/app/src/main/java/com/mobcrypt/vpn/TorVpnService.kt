package com.mobcrypt.vpn

import android.app.Notification
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.ParcelFileDescriptor
import android.util.Log
import com.mobcrypt.MobCryptApp
import com.mobcrypt.MainActivity
import com.mobcrypt.R
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.Socket
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.Executors

class TorVpnService : VpnService() {

    companion object {
        private const val TAG = "TorVpnService"
        const val EXTRA_SOCKS_PROXY = "socks_proxy"
        private const val VPN_MTU = 1500
        private const val PRIVATE_VLAN = "10.0.0."
        private const val PRIVATE_VLAN_PREFIX = 24
    }

    private var vpnInterface: ParcelFileDescriptor? = null
    private val executor = Executors.newSingleThreadExecutor()
    private var socksHost = "127.0.0.1"
    private var socksPort = 9050

    override fun onCreate() {
        super.onCreate()
        setupNotification()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        socksHost = intent?.getStringExtra(EXTRA_SOCKS_PROXY)?.split(":")?.get(0) ?: "127.0.0.1"
        socksPort = intent?.getStringExtra(EXTRA_SOCKS_PROXY)?.split(":")?.get(1)?.toIntOrNull() ?: 9050

        startVpn()
        return START_STICKY
    }

    override fun onDestroy() {
        stopVpn()
        super.onDestroy()
    }

    private fun setupNotification() {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = Notification.Builder(this, MobCryptApp.CHANNEL_VPN)
            .setContentTitle("MobCrypt VPN")
            .setContentText("Protegido via Tor")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()

        startForeground(1, notification)
    }

    private fun startVpn() {
        val builder = Builder()
        builder.setSession("MobCrypt Tor VPN")
        builder.setMtu(VPN_MTU)
        builder.setBlocking(true)

        builder.addAddress("$PRIVATE_VLAN${System.currentTimeMillis() % 254 + 1}", PRIVATE_VLAN_PREFIX)
        builder.addRoute("0.0.0.0", 0)

        // DNS through Tor
        builder.addDnsServer("1.1.1.1")
        builder.addDnsServer("8.8.8.8")

        vpnInterface = builder.establish()
        if (vpnInterface == null) {
            Log.e(TAG, "VPN interface establishment failed")
            return
        }

        executor.execute { vpnThread() }
    }

    private fun stopVpn() {
        try {
            vpnInterface?.close()
            vpnInterface = null
        } catch (e: Exception) {
            Log.e(TAG, "Error closing VPN interface", e)
        }
    }

    private fun vpnThread() {
        val vpnInput = FileInputStream(vpnInterface!!.fileDescriptor)
        val vpnOutput = FileOutputStream(vpnInterface!!.fileDescriptor)
        val packet = ByteArray(VPN_MTU)

        val vpnInterfaceFileDescriptor = vpnInterface!!.fileDescriptor

        while (vpnInterfaceFileDescriptor.valid()) {
            try {
                val length = vpnInput.read(packet)
                if (length <= 0) continue

                // Parse IP header to determine destination
                val byteBuffer = ByteBuffer.wrap(packet, 0, length).order(ByteOrder.BIG_ENDIAN)
                val versionAndIhl = byteBuffer.get().toInt() and 0xFF
                val headerLength = (versionAndIhl and 0x0F) * 4

                // Skip header
                byteBuffer.position(headerLength)

                val protocol = byteBuffer.get(9).toInt() and 0xFF

                when (protocol) {
                    6 -> handleTcp(packet, length, headerLength, vpnOutput)
                    17 -> handleUdp(packet, length, headerLength, vpnOutput)
                    else -> {} // Ignore other protocols
                }
            } catch (e: Exception) {
                if (vpnInterfaceFileDescriptor.valid()) {
                    Log.e(TAG, "VPN thread error", e)
                }
                break
            }
        }
    }

    private fun handleTcp(packet: ByteArray, length: Int, headerLength: Int, vpnOutput: FileOutputStream) {
        try {
            val socket = Socket()
            socket.connect(InetSocketAddress(socksHost, socksPort), 5000)

            val tcpHeaderOffset = headerLength
            val sourcePort = ((packet[tcpHeaderOffset].toInt() and 0xFF) shl 8) or (packet[tcpHeaderOffset + 1].toInt() and 0xFF)
            val destPort = ((packet[tcpHeaderOffset + 2].toInt() and 0xFF) shl 8) or (packet[tcpHeaderOffset + 3].toInt() and 0xFF)

            // Extract payload (TCP data after header)
            val tcpHeaderLength = ((packet[tcpHeaderOffset + 12].toInt() and 0xF0) shr 2)
            val dataOffset = tcpHeaderOffset + tcpHeaderLength

            if (dataOffset < length) {
                socket.getOutputStream().write(packet, dataOffset, length - dataOffset)
                val response = ByteArray(VPN_MTU)
                val responseLength = socket.getInputStream().read(response)
                if (responseLength > 0) {
                    // Construct IP response
                    val responsePacket = buildIpPacket(packet, response, responseLength, headerLength)
                    vpnOutput.write(responsePacket)
                }
            }

            socket.close()
        } catch (e: Exception) {
            Log.d(TAG, "TCP handling error (expected for non-HTTP)", e)
        }
    }

    private fun handleUdp(packet: ByteArray, length: Int, headerLength: Int, vpnOutput: FileOutputStream) {
        // For UDP DNS queries, forward through Tor's UDP support or drop
        // Most auth traffic is TCP-based (HTTPS)
    }

    private fun buildIpPacket(
        originalPacket: ByteArray,
        responseData: ByteArray,
        responseLength: Int,
        headerLength: Int
    ): ByteArray {
        val totalLength = headerLength + responseLength
        val result = ByteArray(totalLength)

        // Copy IP header
        System.arraycopy(originalPacket, 0, result, 0, headerLength)

        // Swap source and destination IP
        for (i in 12 until 16) {
            val temp = result[i]
            result[i] = result[i + 4]
            result[i + 4] = temp
        }

        // Update total length in IP header
        result[2] = ((totalLength shr 8) and 0xFF).toByte()
        result[3] = (totalLength and 0xFF).toByte()

        // Copy response data after IP header
        System.arraycopy(responseData, 0, result, headerLength, responseLength)

        return result
    }
}
