package com.mobcrypt

import android.content.Intent
import android.net.VpnService
import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.switchmaterial.SwitchMaterial
import com.mobcrypt.service.MonitorService
import com.mobcrypt.tor.TorManager
import com.mobcrypt.vpn.TorVpnService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var vpnToggle: SwitchMaterial
    private lateinit var rotationStatus: TextView
    private lateinit var torManager: TorManager

    private val vpnState = MutableStateFlow(VpnState.IDLE)

    private val vpnIntentLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            startVpnService()
        } else {
            vpnState.value = VpnState.IDLE
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        torManager = (application as MobCryptApp).torManager

        vpnToggle = findViewById(R.id.vpnToggle)
        rotationStatus = findViewById(R.id.rotationStatus)

        findViewById<com.google.android.material.button.MaterialButton>(R.id.btnNewIdentity)
            .setOnClickListener { requestNewIdentity() }

        vpnToggle.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked) {
                startVpn()
            } else {
                stopVpn()
            }
        }

        rotationStatus.text = "Rotacao periodica: ativa (240~540s)"

        lifecycleScope.launch {
            vpnState.collect { state ->
                updateUi(state)
            }
        }
    }

    private fun requestNewIdentity() {
        lifecycleScope.launch {
            torManager.requestNewIdentity()
            Toast.makeText(this@MainActivity, "Nova identidade Tor solicitada", Toast.LENGTH_SHORT).show()
        }
    }

    private fun startVpn() {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            vpnIntentLauncher.launch(intent)
        } else {
            startVpnService()
        }
    }

    private fun startVpnService() {
        val intent = Intent(this, TorVpnService::class.java)
        intent.putExtra(TorVpnService.EXTRA_SOCKS_PROXY, torManager.socksProxyAddress)
        startForegroundService(intent)
        vpnState.value = VpnState.CONNECTING

        lifecycleScope.launch {
            torManager.startTor()
            vpnState.value = VpnState.CONNECTED
        }
    }

    private fun stopVpn() {
        val intent = Intent(this, TorVpnService::class.java)
        stopService(intent)
        vpnState.value = VpnState.IDLE
    }

    private fun updateUi(state: VpnState) {
        vpnToggle.isChecked = state == VpnState.CONNECTED || state == VpnState.CONNECTING
    }

    enum class VpnState {
        IDLE, CONNECTING, CONNECTED
    }
}
