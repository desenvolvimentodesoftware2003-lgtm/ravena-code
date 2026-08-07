package com.mobcrypt

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.mobcrypt.tor.TorManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class MobCryptApp : Application() {

    lateinit var torManager: TorManager
        private set

    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onCreate() {
        super.onCreate()
        instance = this
        createNotificationChannels()
        torManager = TorManager(this)
        torManager.startRotation(appScope)
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_VPN,
                "MobCrypt VPN",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Rotacao de identidade Tor ativa"
            }
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }
    }

    companion object {
        const val CHANNEL_VPN = "mobcrypt_vpn"

        lateinit var instance: MobCryptApp
            private set
    }
}
