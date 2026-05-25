package com.example.booktrail_mobile

import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity(), NfcAdapter.ReaderCallback {
    private var nfcAdapter: NfcAdapter? = null
    private var pendingScanResult: MethodChannel.Result? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            NFC_CHANNEL,
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "isAvailable" -> result.success(isNfcAvailable())
                "scanTag" -> handleScanTag(result)
                else -> result.notImplemented()
            }
        }
    }

    override fun onPause() {
        super.onPause()
        disableReaderMode()
    }

    override fun onTagDiscovered(tag: Tag) {
        val result = pendingScanResult ?: return
        val uid = tag.id?.toHexUid().orEmpty()

        runOnUiThread {
            disableReaderMode()
            pendingScanResult = null

            if (uid.isBlank()) {
                result.error("empty_uid", "Не удалось прочитать UID NFC-метки.", null)
                return@runOnUiThread
            }

            result.success(
                mapOf(
                    "uid" to uid,
                    "techList" to tag.techList.toList(),
                ),
            )
        }
    }

    private fun handleScanTag(result: MethodChannel.Result) {
        val adapter = nfcAdapter
        if (adapter == null) {
            result.error("not_supported", "Устройство не поддерживает NFC.", null)
            return
        }

        if (!adapter.isEnabled) {
            result.error("disabled", "NFC выключен на устройстве.", null)
            return
        }

        if (pendingScanResult != null) {
            result.error("scan_in_progress", "Сканирование NFC уже запущено.", null)
            return
        }

        pendingScanResult = result
        enableReaderMode(adapter)
    }

    private fun isNfcAvailable(): Boolean {
        val adapter = nfcAdapter ?: return false
        return adapter.isEnabled
    }

    private fun enableReaderMode(adapter: NfcAdapter) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.KITKAT) {
            pendingScanResult?.error(
                "unsupported_android",
                "Reader mode требует Android 4.4 или новее.",
                null,
            )
            pendingScanResult = null
            return
        }

        adapter.enableReaderMode(
            this,
            this,
            NFC_FLAGS,
            Bundle().apply {
                putInt(NfcAdapter.EXTRA_READER_PRESENCE_CHECK_DELAY, 250)
            },
        )
    }

    private fun disableReaderMode() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            nfcAdapter?.disableReaderMode(this)
        }
    }

    private fun ByteArray.toHexUid(): String = joinToString(separator = "") { byte ->
        "%02X".format(byte)
    }

    companion object {
        private const val NFC_CHANNEL = "booktrail/nfc"
        private const val NFC_FLAGS =
            NfcAdapter.FLAG_READER_NFC_A or
                NfcAdapter.FLAG_READER_NFC_B or
                NfcAdapter.FLAG_READER_NFC_F or
                NfcAdapter.FLAG_READER_NFC_V or
                NfcAdapter.FLAG_READER_NFC_BARCODE or
                NfcAdapter.FLAG_READER_SKIP_NDEF_CHECK
    }
}
