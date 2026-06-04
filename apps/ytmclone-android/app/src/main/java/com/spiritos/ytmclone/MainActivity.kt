package com.spiritos.ytmclone

import android.annotation.SuppressLint
import android.app.Notification
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID

private const val YTM_URL = "https://music.youtube.com"
private const val DEFAULT_BACKEND_URL = "http://192.168.1.50:3000"

class MainActivity : ComponentActivity() {
    private lateinit var reporter: EventReporter
    private val sessionId = UUID.randomUUID().toString()
    private val currentTrack = mutableStateOf("No track detected yet")
    private val connectionStatus = mutableStateOf("SpiritOS: checking")
    private var webView: WebView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        reporter = EventReporter(this)
        reporter.enqueue(
            YtmEvent(
                eventType = "app_open",
                deviceId = reporter.deviceId,
                sessionId = sessionId,
                source = "android-app",
            )
        )

        lifecycleScope.launch {
            while (true) {
                connectionStatus.value = if (reporter.flush()) "SpiritOS: connected" else "SpiritOS: queued"
                delay(15000)
            }
        }

        setContent {
            MaterialTheme {
                Surface(color = Color(0xff09090b), modifier = Modifier.fillMaxSize()) {
                    YtmCloneApp(
                        currentTrack = currentTrack.value,
                        connectionStatus = connectionStatus.value,
                        backendUrl = reporter.backendUrl,
                        onBackendUrlChange = {
                            reporter.backendUrl = it
                            lifecycleScope.launch { connectionStatus.value = if (reporter.flush()) "SpiritOS: connected" else "SpiritOS: queued" }
                        },
                        onOpenStats = { openUri("${reporter.backendUrl.trimEnd('/')}/stats") },
                        onOpenNotificationSettings = { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) },
                        onOpenOfficialYtm = { openUri(YTM_URL) },
                        onWebView = { webView = it },
                        webViewFactory = { createYtmWebView() },
                    )
                }
            }
        }
    }

    override fun onPause() {
        CookieManager.getInstance().flush()
        super.onPause()
    }

    private fun openUri(url: String) {
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun createYtmWebView(): WebView {
        return WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.mediaPlaybackRequiresUserGesture = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.userAgentString = "${settings.userAgentString} SpiritOS-YTMClone/0.1"

            CookieManager.getInstance().setAcceptCookie(true)
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)
            addJavascriptInterface(Bridge(), "SpiritYtmBridge")

            webChromeClient = WebChromeClient()
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                    return false
                }

                override fun onPageFinished(view: WebView, url: String) {
                    super.onPageFinished(view, url)
                    injectBridge(view)
                    reporter.enqueue(
                        YtmEvent(
                            eventType = "ytm_loaded",
                            deviceId = reporter.deviceId,
                            sessionId = sessionId,
                            source = "android-webview",
                            sourceUrl = url,
                        )
                    )
                }
            }
            loadUrl(YTM_URL)
        }
    }

    private fun injectBridge(view: WebView) {
        view.evaluateJavascript(YTM_TRACKER_SCRIPT, null)
    }

    inner class Bridge {
        @JavascriptInterface
        fun postEvent(json: String) {
            try {
                val obj = JSONObject(json)
                val event = YtmEvent(
                    eventType = obj.optString("eventType", "now_playing"),
                    deviceId = reporter.deviceId,
                    sessionId = sessionId,
                    source = "android-webview",
                    title = obj.optString("title").ifBlank { null },
                    artist = obj.optString("artist").ifBlank { null },
                    album = obj.optString("album").ifBlank { null },
                    thumbnailUrl = obj.optString("thumbnailUrl").ifBlank { null },
                    videoId = obj.optString("videoId").ifBlank { null },
                    watchUrl = obj.optString("watchUrl").ifBlank { null },
                    sourceUrl = obj.optString("sourceUrl").ifBlank { null },
                    playbackState = obj.optString("playbackState").ifBlank { null },
                    positionSeconds = obj.optDoubleOrNull("positionSeconds"),
                    durationSeconds = obj.optDoubleOrNull("durationSeconds"),
                    raw = obj.toString(),
                )
                reporter.enqueue(event)
                if (!event.title.isNullOrBlank()) {
                    runOnUiThread {
                        currentTrack.value = listOfNotNull(event.title, event.artist).joinToString(" - ")
                    }
                }
            } catch (error: Throwable) {
                reporter.enqueue(
                    YtmEvent(
                        eventType = "bridge_error",
                        deviceId = reporter.deviceId,
                        sessionId = sessionId,
                        source = "android-webview",
                        raw = error.message,
                    )
                )
            }
        }
    }
}

@Composable
private fun YtmCloneApp(
    currentTrack: String,
    connectionStatus: String,
    backendUrl: String,
    onBackendUrlChange: (String) -> Unit,
    onOpenStats: () -> Unit,
    onOpenNotificationSettings: () -> Unit,
    onOpenOfficialYtm: () -> Unit,
    onWebView: (WebView) -> Unit,
    webViewFactory: () -> WebView,
) {
    var showSettings by remember { mutableStateOf(false) }
    var showDiagnostics by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val webView = remember { webViewFactory() }

    DisposableEffect(webView) {
        onWebView(webView)
        onDispose { webView.destroy() }
    }

    BackHandler(enabled = webView.canGoBack()) {
        webView.goBack()
    }

    Column(modifier = Modifier.fillMaxSize().background(Color(0xff09090b))) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xff18181b))
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = connectionStatus,
                    color = Color(0xff67e8f9),
                    modifier = Modifier.weight(1f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                TextButton(onClick = onOpenStats) { Text("Stats") }
                TextButton(onClick = { showSettings = true }) { Text("URL") }
                TextButton(onClick = { showDiagnostics = true }) { Text("Diag") }
            }
            Text(
                text = currentTrack,
                color = Color.White,
                fontWeight = FontWeight.SemiBold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }

        AndroidView(
            factory = { webView },
            modifier = Modifier.fillMaxSize(),
        )
    }

    if (showSettings) {
        BackendDialog(
            backendUrl = backendUrl,
            onDismiss = { showSettings = false },
            onSave = {
                onBackendUrlChange(it)
                showSettings = false
            },
        )
    }

    if (showDiagnostics) {
        AlertDialog(
            onDismissRequest = { showDiagnostics = false },
            title = { Text("Diagnostics") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("If embedded sign-in or DOM tracking is blocked, enable notification access for YTMClone and play music in the official YouTube Music app.")
                    Text("Phone path: Settings -> Notifications -> Advanced settings -> Notification history/access may vary by One UI version; use the button below for Android's Notification Access screen.")
                }
            },
            confirmButton = {
                Button(onClick = onOpenNotificationSettings) { Text("Notification Access") }
            },
            dismissButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = onOpenOfficialYtm) { Text("Open YTM") }
                    TextButton(onClick = { showDiagnostics = false }) { Text("Close") }
                }
            },
        )
    }

    LaunchedEffect(context) {
        CookieManager.getInstance().flush()
    }
}

@Composable
private fun BackendDialog(backendUrl: String, onDismiss: () -> Unit, onSave: (String) -> Unit) {
    var value by remember(backendUrl) { mutableStateOf(backendUrl) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("SpiritOS backend") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Set the Dell LAN URL that serves SpiritOS.")
                OutlinedTextField(
                    value = value,
                    onValueChange = { value = it },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
                    label = { Text("Backend URL") },
                )
            }
        },
        confirmButton = { Button(onClick = { onSave(value.trim()) }) { Text("Save") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

data class YtmEvent(
    val eventType: String,
    val deviceId: String,
    val sessionId: String,
    val source: String,
    val capturedAt: String = java.time.Instant.now().toString(),
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val thumbnailUrl: String? = null,
    val videoId: String? = null,
    val watchUrl: String? = null,
    val sourceUrl: String? = null,
    val playbackState: String? = null,
    val positionSeconds: Double? = null,
    val durationSeconds: Double? = null,
    val raw: String? = null,
) {
    fun toJson(): JSONObject {
        val idBasis = listOf(eventType, capturedAt, deviceId, sessionId, title, artist, videoId).joinToString("|")
        return JSONObject().apply {
            put("eventId", sha256(idBasis))
            put("eventType", eventType)
            put("capturedAt", capturedAt)
            put("deviceId", deviceId)
            put("sessionId", sessionId)
            put("source", source)
            putOpt("title", title)
            putOpt("artist", artist)
            putOpt("album", album)
            putOpt("thumbnailUrl", thumbnailUrl)
            putOpt("videoId", videoId)
            putOpt("watchUrl", watchUrl)
            putOpt("sourceUrl", sourceUrl)
            putOpt("playbackState", playbackState)
            putOpt("positionSeconds", positionSeconds)
            putOpt("durationSeconds", durationSeconds)
            putOpt("raw", raw)
        }
    }
}

class EventReporter(private val context: Context) {
    private val prefs = context.getSharedPreferences("ytmclone", Context.MODE_PRIVATE)
    private var lastFingerprint: String? = null

    val deviceId: String = prefs.getString("deviceId", null) ?: UUID.randomUUID().toString().also {
        prefs.edit().putString("deviceId", it).apply()
    }

    var backendUrl: String
        get() = prefs.getString("backendUrl", DEFAULT_BACKEND_URL) ?: DEFAULT_BACKEND_URL
        set(value) {
            prefs.edit().putString("backendUrl", value.ifBlank { DEFAULT_BACKEND_URL }).apply()
        }

    fun enqueue(event: YtmEvent) {
        val fingerprint = listOf(event.eventType, event.title, event.artist, event.videoId, event.playbackState).joinToString("|")
        if (fingerprint == lastFingerprint && event.eventType in setOf("now_playing", "heartbeat", "play_state")) {
            return
        }
        lastFingerprint = fingerprint

        val queue = readQueue()
        queue.put(event.toJson())
        prefs.edit().putString("queue", queue.toString()).apply()
    }

    suspend fun flush(): Boolean = withContext(Dispatchers.IO) {
        val queue = readQueue()
        if (queue.length() == 0) return@withContext testConnection()

        val payload = JSONObject().put("events", queue)
        val ok = postJson("${backendUrl.trimEnd('/')}/api/ytmclone/stats/events", payload)
        if (ok) {
            prefs.edit().putString("queue", "[]").apply()
        }
        ok
    }

    private fun readQueue(): JSONArray {
        return try {
            JSONArray(prefs.getString("queue", "[]") ?: "[]")
        } catch (_: Throwable) {
            JSONArray()
        }
    }

    private fun testConnection(): Boolean {
        return try {
            val connection = URL("${backendUrl.trimEnd('/')}/api/ytmclone/stats/summary").openConnection() as HttpURLConnection
            connection.requestMethod = "GET"
            connection.connectTimeout = 2500
            connection.readTimeout = 2500
            connection.responseCode in 200..299
        } catch (_: Throwable) {
            false
        }
    }

    private fun postJson(url: String, payload: JSONObject): Boolean {
        return try {
            val connection = URL(url).openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 4000
            connection.readTimeout = 4000
            connection.doOutput = true
            connection.setRequestProperty("content-type", "application/json")
            OutputStreamWriter(connection.outputStream).use { it.write(payload.toString()) }
            connection.responseCode in 200..299
        } catch (_: Throwable) {
            false
        }
    }
}

class YtmNotificationListener : NotificationListenerService() {
    private lateinit var reporter: EventReporter
    private val sessionId = "notification-${UUID.randomUUID()}"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        reporter = EventReporter(this)
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (!sbn.packageName.contains("youtube", ignoreCase = true)) return
        val extras = sbn.notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()
        val artist = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()
        if (title.isNullOrBlank() && artist.isNullOrBlank()) return

        reporter.enqueue(
            YtmEvent(
                eventType = "now_playing",
                deviceId = reporter.deviceId,
                sessionId = sessionId,
                source = "android-notification",
                title = title,
                artist = artist,
                playbackState = "notification",
                raw = sbn.packageName,
            )
        )
        scope.launch { reporter.flush() }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}

private fun JSONObject.optDoubleOrNull(name: String): Double? {
    return if (has(name) && !isNull(name)) optDouble(name).takeIf { !it.isNaN() } else null
}

private fun sha256(value: String): String {
    val digest = MessageDigest.getInstance("SHA-256").digest(value.toByteArray())
    return digest.joinToString("") { "%02x".format(it) }
}

private val YTM_TRACKER_SCRIPT = """
(function () {
  if (window.__spiritYtmTrackerInstalled) return;
  window.__spiritYtmTrackerInstalled = true;

  const state = { lastKey: "", lastTrackAt: 0, lastPosition: null };
  const text = (selector) => {
    const node = document.querySelector(selector);
    return node && node.textContent ? node.textContent.trim().replace(/\s+/g, " ") : "";
  };
  const attr = (selector, name) => {
    const node = document.querySelector(selector);
    return node ? (node.getAttribute(name) || "") : "";
  };
  const seconds = (value) => {
    if (!value || !value.includes(":")) return null;
    return value.split(":").map(Number).reduce((acc, part) => acc * 60 + (Number.isFinite(part) ? part : 0), 0);
  };
  const videoId = () => {
    try {
      const url = new URL(location.href);
      return url.searchParams.get("v") || "";
    } catch (error) {
      return "";
    }
  };
  const snapshot = (eventType) => {
    const title = text("ytmusic-player-bar .title") || text(".ytmusic-player-bar .title") || text("yt-formatted-string.title");
    const artist = text("ytmusic-player-bar .byline") || text(".ytmusic-player-bar .byline") || text("yt-formatted-string.byline");
    const album = text("ytmusic-player-bar .subtitle yt-formatted-string:nth-child(2)");
    const thumbnailUrl = attr("ytmusic-player-bar img", "src") || attr(".ytmusic-player-bar img", "src");
    const playButtonLabel = attr("ytmusic-player-bar #play-pause-button", "aria-label") || attr("#play-pause-button", "aria-label");
    const position = seconds(text(".time-info .time-info-current") || text("#left-controls .time-info-current"));
    const duration = seconds(text(".time-info .time-info-duration") || text("#left-controls .time-info-duration"));
    const playbackState = /pause/i.test(playButtonLabel) ? "playing" : /play/i.test(playButtonLabel) ? "paused" : "";

    return {
      eventType,
      title,
      artist,
      album,
      thumbnailUrl,
      videoId: videoId(),
      watchUrl: location.href,
      sourceUrl: location.href,
      playbackState,
      positionSeconds: position,
      durationSeconds: duration,
      capturedAt: new Date().toISOString()
    };
  };
  const post = (payload) => {
    try {
      window.SpiritYtmBridge.postEvent(JSON.stringify(payload));
    } catch (error) {}
  };
  const emit = (reason) => {
    const payload = snapshot("now_playing");
    if (!payload.title && !payload.videoId) return;
    const key = [payload.title, payload.artist, payload.videoId, payload.playbackState].join("|");
    if (key === state.lastKey && state.lastPosition !== null && payload.positionSeconds < state.lastPosition - 20) {
      post({ ...payload, eventType: "possible_replay" });
    }
    if (key !== state.lastKey) {
      const now = Date.now();
      if (state.lastKey && now - state.lastTrackAt < 45000) post({ ...payload, eventType: "possible_skip" });
      post({ ...payload, eventType: state.lastKey ? "track_changed" : "now_playing" });
      state.lastKey = key;
      state.lastTrackAt = now;
    } else if (reason === "heartbeat") {
      post({ ...payload, eventType: "heartbeat" });
    }
    if (payload.playbackState === "playing") post({ ...payload, eventType: "play_state" });
    if (payload.playbackState === "paused") post({ ...payload, eventType: "pause_state" });
    state.lastPosition = payload.positionSeconds;
  };

  const observer = new MutationObserver(() => emit("mutation"));
  observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true });
  setInterval(() => emit("heartbeat"), 30000);
  setTimeout(() => emit("initial"), 2500);
})();
""".trimIndent()
