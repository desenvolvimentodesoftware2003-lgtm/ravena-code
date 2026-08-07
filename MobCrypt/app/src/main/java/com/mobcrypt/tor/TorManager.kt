package com.mobcrypt.tor

import android.content.Context
import android.content.Intent
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.net.InetSocketAddress
import java.net.Socket
import kotlin.random.Random

class TorManager(private val context: Context) {

    companion object {
        private const val TAG = "TorManager"
        const val SOCKS_HOST = "127.0.0.1"
        const val SOCKS_PORT = 9050
        const val HTTP_HOST = "127.0.0.1"
        const val HTTP_PORT = 8118
        const val SOCKS_PROXY = "$SOCKS_HOST:$SOCKS_PORT"
        const val ORBOT_PACKAGE = "org.torproject.android"
        const val ORBOT_PROXY_PORT = 9050
        const val MIN_INTERVAL = 240.0
        const val MAX_INTERVAL = 540.0
    }

    val socksProxyAddress: String get() = "$SOCKS_HOST:$SOCKS_PORT"
    val httpProxyAddress: String get() = "$HTTP_HOST:$HTTP_PORT"

    private var torProcess: Process? = null
    private var isRunning = false
    private var rotationJob: Job? = null

    suspend fun startTor(): Boolean = withContext(Dispatchers.IO) {
        if (isRunning) return@withContext true

        try {
            if (isOrbotInstalled()) {
                startOrbot()
            } else {
                startEmbeddedTor()
            }
            isRunning = true
            Log.d(TAG, "Tor started successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start Tor", e)
            false
        }
    }

    suspend fun stopTor(): Boolean = withContext(Dispatchers.IO) {
        try {
            rotationJob?.cancel()
            rotationJob = null
            torProcess?.destroy()
            torProcess = null
            isRunning = false
            Log.d(TAG, "Tor stopped")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping Tor", e)
            false
        }
    }

    suspend fun requestNewIdentity(): Boolean = withContext(Dispatchers.IO) {
        try {
            val socket = Socket()
            socket.connect(InetSocketAddress(SOCKS_HOST, SOCKS_PORT), 3000)
            val command = "AUTHENTICATE\r\nSIGNAL NEWNYM\r\n"
            socket.getOutputStream().write(command.toByteArray())
            socket.close()
            Log.d(TAG, "New Tor identity requested")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to request new identity", e)
            false
        }
    }

    private fun generateRotationDelay(): Long {
        val raw = Random.nextDouble(MIN_INTERVAL, MAX_INTERVAL)
        val seconds = raw.toInt()
        val millis = Random.nextInt(1, 1000)
        return seconds * 1000L + millis
    }

    fun formatRotationDelay(ms: Long): String {
        val totalSecs = ms / 1000
        val mins = totalSecs / 60
        val secs = totalSecs % 60
        val millis = ms % 1000
        return "%02dmin%02ds%03dms".format(mins, secs, millis)
    }

    fun startRotation(scope: CoroutineScope) {
        rotationJob?.cancel()
        rotationJob = scope.launch(Dispatchers.IO) {
            while (isActive) {
                val interval = generateRotationDelay()
                Log.d(TAG, "Proxima rotacao em ${formatRotationDelay(interval)}")
                delay(interval)
                Log.d(TAG, "Rodando nova identidade Tor...")
                requestNewIdentity()
            }
        }
        Log.d(TAG, "Rotacao periodica iniciada ($MIN_INTERVAL-$MAX_INTERVAL s)")
    }

    fun stopRotation() {
        rotationJob?.cancel()
        rotationJob = null
        Log.d(TAG, "Rotacao periodica parada")
    }

    fun isRunning(): Boolean = isRunning

    private fun isOrbotInstalled(): Boolean {
        return try {
            context.packageManager.getPackageInfo(ORBOT_PACKAGE, 0)
            true
        } catch (e: Exception) {
            false
        }
    }

    private fun startOrbot() {
        val intent = context.packageManager.getLaunchIntentForPackage(ORBOT_PACKAGE)
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            intent.putExtra("org.torproject.android.intent.extra.START", true)
            context.startActivity(intent)
        }
    }

    private fun startEmbeddedTor() {
        val torBinary = extractTorBinary()
        if (torBinary == null) {
            Log.w(TAG, "Tor binary not available, using Orbot proxy mode")
            return
        }

        val dataDir = File(context.filesDir, "tor")
        dataDir.mkdirs()

        val configFile = File(dataDir, "torrc").apply {
            writeText("""
                SocksPort $SOCKS_PORT
                ControlPort 9051
                DataDirectory $dataDir
                CookieAuthentication 1
                Log notice syslog
            """.trimIndent())
        }

        val pb = ProcessBuilder(
            torBinary.absolutePath,
            "-f", configFile.absolutePath
        ).apply {
            environment()["HOME"] = dataDir.absolutePath
            redirectErrorStream(true)
        }

        torProcess = pb.start()
    }

    private fun extractTorBinary(): File? {
        val torFile = File(context.filesDir, "tor/bin/tor")
        if (torFile.exists()) return torFile

        try {
            val inputStream = context.assets.open("tor/tor")
            torFile.parentFile?.mkdirs()
            FileOutputStream(torFile).use { output ->
                inputStream.copyTo(output)
            }
            torFile.setExecutable(true)
            return torFile
        } catch (e: Exception) {
            Log.e(TAG, "Could not extract Tor binary", e)
            return null
        }
    }

    fun configureProxy() {
        System.setProperty("socksProxyHost", SOCKS_HOST)
        System.setProperty("socksProxyPort", SOCKS_PORT.toString())
        System.setProperty("http.proxyHost", HTTP_HOST)
        System.setProperty("http.proxyPort", HTTP_PORT.toString())
        System.setProperty("https.proxyHost", HTTP_HOST)
        System.setProperty("https.proxyPort", HTTP_PORT.toString())
    }
}
