package com.mobcrypt.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import com.mobcrypt.MobCryptApp
import com.mobcrypt.MainActivity
import com.mobcrypt.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class MonitorService : Service() {

    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var monitorJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(createNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        monitorJob?.cancel()
        monitorJob = scope.launch {
            monitorLoop()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        monitorJob?.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun monitorLoop() {
        while (isActive) {
            try {
                val torManager = (application as MobCryptApp).torManager
                if (!torManager.isRunning()) {
                    Log.d(TAG, "Tor not running, attempting restart...")
                    kotlinx.coroutines.runBlocking {
                        torManager.startTor()
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Monitor error", e)
            }
            kotlinx.coroutines.runBlocking {
                delay(TOR_CHECK_INTERVAL)
            }
        }
    }

    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return Notification.Builder(this, MobCryptApp.CHANNEL_MONITOR)
            .setContentTitle("MobCrypt Monitor")
            .setContentText("Monitorando autenticações...")
            .setSmallIcon(android.R.drawable.ic_menu_manage)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val TAG = "MonitorService"
        private const val TOR_CHECK_INTERVAL = 30_000L // 30 seconds
    }
}
