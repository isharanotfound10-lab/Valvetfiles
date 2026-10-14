from pathlib import Path

root = Path("native-project/app")
gradle = root / "build.gradle.kts"
source = root / "src/main/java/com/velvetfiles/app/MainActivity.kt"

g = gradle.read_text()
dep = '    implementation("org.videolan.android:libvlc-all:3.6.5")'
if dep not in g:
    if "dependencies {\n" not in g:
        raise SystemExit("Could not locate app dependencies block")
    g = g.replace("dependencies {\n", "dependencies {\n" + dep + "\n", 1)
g = g.replace("versionCode = 6", "versionCode = 7").replace('versionName = "1.5"', 'versionName = "1.6"')
abi = '        ndk { abiFilters += setOf("arm64-v8a", "armeabi-v7a") }'
if abi not in g:
    g = g.replace('versionName = "1.6"\n', 'versionName = "1.6"\n' + abi + '\n', 1)
gradle.write_text(g)

s = source.read_text()
old_call = 'VideoPlayerPanel(file, queue.filter { isVideoFile(it) }, Modifier.weight(1f).fillMaxWidth(), onNavigate, onVideoProgress)'
new_call = 'VlcVideoPlayerPanel(file, queue.filter { isVideoFile(it) }, Modifier.weight(1f).fillMaxWidth(), onNavigate, onVideoProgress)'
if new_call not in s:
    if old_call not in s:
        raise SystemExit("Could not locate existing video-player call")
    s = s.replace(old_call, new_call, 1)

marker = '@Composable\nprivate fun VideoPlayerPanel('
if 'private fun VlcVideoPlayerPanel(' not in s:
    if marker not in s:
        raise SystemExit("Could not locate VideoPlayerPanel insertion point")
    component = r'''@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VlcVideoPlayerPanel(
    file: File,
    queue: List<File>,
    modifier: Modifier,
    onNavigate: (File) -> Unit,
    onPosition: (String, Int, Int) -> Unit
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("file_manager_preferences", Context.MODE_PRIVATE) }
    val activity = context as? Activity
    val audioManager = remember { context.getSystemService(Context.AUDIO_SERVICE) as AudioManager }
    val libVlc = remember(file.absolutePath, context) {
        org.videolan.libvlc.LibVLC(context, arrayListOf(
            "--audio-time-stretch", "--avcodec-hw=any", "--network-caching=1200",
            "--file-caching=400", "--sub-autodetect-file", "--no-video-title-show",
            "--drop-late-frames", "--skip-frames"
        ))
    }
    val player = remember(libVlc) { org.videolan.libvlc.MediaPlayer(libVlc) }
    var playing by remember(file.absolutePath) { mutableStateOf(false) }
    var ready by remember(file.absolutePath) { mutableStateOf(false) }
    var position by remember(file.absolutePath) { mutableIntStateOf(0) }
    var duration by remember(file.absolutePath) { mutableIntStateOf(1) }
    var speed by remember(file.absolutePath) { mutableFloatStateOf(1f) }
    var aspect by remember(file.absolutePath) { mutableStateOf("Default") }
    var locked by remember(file.absolutePath) { mutableStateOf(false) }
    var showControls by remember(file.absolutePath) { mutableStateOf(true) }
    var fullscreen by remember(file.absolutePath) { mutableStateOf(false) }
    var menu by remember(file.absolutePath) { mutableStateOf("") }
    var audioTracks by remember(file.absolutePath) { mutableStateOf<List<Pair<Int, String>>>(emptyList()) }
    var subtitleTracks by remember(file.absolutePath) { mutableStateOf<List<Pair<Int, String>>>(emptyList()) }
    var gestureMeter by remember(file.absolutePath) { mutableStateOf("") }
    var gesturePercent by remember(file.absolutePath) { mutableIntStateOf(50) }
    var audioDelayMs by remember(file.absolutePath) { mutableIntStateOf(0) }
    var subtitleDelayMs by remember(file.absolutePath) { mutableIntStateOf(0) }
    var pointA by remember(file.absolutePath) { mutableLongStateOf(-1L) }
    var pointB by remember(file.absolutePath) { mutableLongStateOf(-1L) }
    var repeatVideo by remember(file.absolutePath) { mutableStateOf(false) }
    var message by remember(file.absolutePath) { mutableStateOf("VLC engine · broad format support") }
    val subtitlePicker = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            val added = runCatching { player.addSlave(0, uri, true) }.getOrDefault(false)
            message = if (added) "External subtitle added" else "Couldn't load that subtitle"
        }
    }
    val oldOrientation = remember { activity?.requestedOrientation ?: ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED }
    val oldSystemUi = remember { activity?.window?.decorView?.systemUiVisibility ?: 0 }

    DisposableEffect(player, libVlc, file.absolutePath) {
        activity?.window?.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        onDispose {
            val saved = runCatching { player.time.toInt().coerceAtLeast(0) }.getOrDefault(position)
            prefs.edit().putInt("video_position:" + file.absolutePath, saved).apply()
            runCatching { player.stop() }
            runCatching { player.detachViews() }
            runCatching { player.release() }
            runCatching { libVlc.release() }
            activity?.requestedOrientation = oldOrientation
            @Suppress("DEPRECATION")
            run { activity?.window?.decorView?.systemUiVisibility = oldSystemUi }
            activity?.window?.clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
    }
    DisposableEffect(fullscreen) {
        val decor = activity?.window?.decorView
        if (fullscreen && activity != null && decor != null) {
            if (Build.VERSION.SDK_INT >= 30) activity.window.insetsController?.let {
                it.hide(android.view.WindowInsets.Type.systemBars())
                it.systemBarsBehavior = android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            } else {
                @Suppress("DEPRECATION")
                decor.systemUiVisibility = (View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_STABLE)
            }
            activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        } else if (activity != null && decor != null) {
            if (Build.VERSION.SDK_INT >= 30) activity.window.insetsController?.show(android.view.WindowInsets.Type.systemBars())
            @Suppress("DEPRECATION")
            run { decor.systemUiVisibility = (decor.systemUiVisibility and (View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY).inv()) }
            activity.requestedOrientation = oldOrientation
        }
        onDispose {}
    }
    LaunchedEffect(player, file.absolutePath) {
        var restored = false
        var lastSaved = 0
        var lastReported = -4000
        while (true) {
            val len = runCatching { player.length.coerceAtLeast(1L) }.getOrDefault(1L).coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
            val now = runCatching { player.time.coerceAtLeast(0L) }.getOrDefault(0L).coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
            if (len > 1) {
                duration = len
                ready = true
                if (!restored) {
                    val saved = prefs.getInt("video_position:" + file.absolutePath, 0)
                    if (saved > 1500 && saved < len - 1500) runCatching { player.time = saved.toLong() }
                    restored = true
                }
            }
            position = now.coerceAtMost(duration)
            playing = runCatching { player.isPlaying }.getOrDefault(false)
            if (ready && (kotlin.math.abs(now - lastReported) >= 3000 || now < lastReported)) {
                onPosition(file.absolutePath, position, duration)
                lastReported = now
            }
            if (ready && (kotlin.math.abs(now - lastSaved) >= 4000 || now < lastSaved)) {
                prefs.edit().putInt("video_position:" + file.absolutePath, now).apply()
                lastSaved = now
            }
            if (ready && pointA >= 0 && pointB > pointA && now.toLong() >= pointB) runCatching { player.time = pointA }
            if (ready && repeatVideo && !playing && now >= duration - 1200) runCatching { player.time = 0L; player.play() }
            if (ready && !playing && now >= duration - 1200) prefs.edit().remove("video_position:" + file.absolutePath).apply()
            if (ready && (menu == "audio" || menu == "subtitle")) {
                audioTracks = runCatching { player.audioTracks?.map { it.id to (it.name ?: "Audio track " + it.id) } ?: emptyList() }.getOrDefault(emptyList())
                subtitleTracks = runCatching { player.spuTracks?.map { it.id to (it.name ?: "Subtitle " + it.id) } ?: emptyList() }.getOrDefault(emptyList())
            }
            delay(450)
        }
    }
    LaunchedEffect(gestureMeter) { if (gestureMeter.isNotEmpty()) { delay(1100); gestureMeter = "" } }
    val index = queue.indexOfFirst { it.absolutePath == file.absolutePath }
    val previous = queue.getOrNull(index - 1)
    val next = queue.getOrNull(index + 1)

    Box(modifier.clip(RoundedCornerShape(22.dp)).background(Color.Black)
        .pointerInput(file.absolutePath, locked, ready, duration) {
            detectTapGestures(
                onTap = { if (locked) { locked = false; showControls = true } else showControls = !showControls },
                onDoubleTap = { point ->
                    if (!locked && ready) {
                        val delta = if (point.x < size.width / 2f) -10_000L else 10_000L
                        val target = (player.time + delta).coerceIn(0L, duration.toLong())
                        runCatching { player.time = target }
                        position = target.toInt()
                    }
                }
            )
        }
        .pointerInput(file.absolutePath, locked, ready) {
            var startX = 0f
            var accumulatedY = 0f
            var startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
            detectDragGestures(onDragStart = { startX = it.x; accumulatedY = 0f; startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) }, onDrag = { change, drag ->
                if (!locked && abs(drag.x) <= abs(drag.y) * 1.25f) {
                    change.consume()
                    accumulatedY += drag.y
                    if (startX > size.width * .58f) {
                        val maxVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC).coerceAtLeast(1)
                        val volume = (startingVolume - (accumulatedY / 28f).roundToInt()).coerceIn(0, maxVol)
                        audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, volume, 0)
                        gestureMeter = "volume"
                        gesturePercent = (volume * 100f / maxVol).roundToInt()
                    } else {
                        val attrs = activity?.window?.attributes
                        if (attrs != null) {
                            val base = if (attrs.screenBrightness < 0) .55f else attrs.screenBrightness
                            val brightness = (base - drag.y / 900f).coerceIn(.05f, 1f)
                            attrs.screenBrightness = brightness
                            activity.window.attributes = attrs
                            gestureMeter = "brightness"
                            gesturePercent = (brightness * 100f).roundToInt()
                        }
                    }
                }
            })
        }) {
        AndroidView(factory = { ctx ->
            org.videolan.libvlc.util.VLCVideoLayout(ctx).also { layout ->
                player.attachViews(layout, null, false, false)
                val media = org.videolan.libvlc.Media(libVlc, Uri.fromFile(file))
                media.addOption(":sub-autodetect-file")
                media.addOption(":input-repeat=0")
                player.media = media
                media.release()
                player.play()
            }
        }, modifier = Modifier.fillMaxSize())
        if (gestureMeter == "brightness") VideoGestureMeter("brightness", gesturePercent, Modifier.align(Alignment.CenterStart).padding(start = 20.dp))
        if (gestureMeter == "volume") VideoGestureMeter("volume", gesturePercent, Modifier.align(Alignment.CenterEnd).padding(end = 20.dp))
        if (locked) {
            IconButton(onClick = { locked = false; showControls = true }, modifier = Modifier.align(Alignment.TopEnd).padding(8.dp).background(Color.Black.copy(alpha = .65f), CircleShape)) { Icon(Icons.Default.LockOpen, "Unlock player", tint = Color.White) }
        } else if (showControls) {
            Row(Modifier.align(Alignment.TopEnd).padding(7.dp).background(Color.Black.copy(alpha = .56f), RoundedCornerShape(16.dp)), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { locked = true; showControls = false }) { Icon(Icons.Default.Lock, "Lock controls", tint = Color.White) }
                IconButton(onClick = { fullscreen = !fullscreen }) { Icon(if (fullscreen) Icons.Default.FullscreenExit else Icons.Default.Fullscreen, "Toggle fullscreen", tint = Color.White) }
            }
            Column(Modifier.align(Alignment.BottomCenter).fillMaxWidth().background(Brush.verticalGradient(listOf(Color.Transparent, Color.Black.copy(alpha = .90f)))).padding(horizontal = 8.dp, vertical = 6.dp)) {
                Slider(value = position.toFloat().coerceIn(0f, duration.toFloat()), onValueChange = { position = it.toInt() }, onValueChangeFinished = { runCatching { player.time = position.toLong() } }, valueRange = 0f..duration.toFloat(), enabled = ready, colors = SliderDefaults.colors(thumbColor = Purple, activeTrackColor = Purple, inactiveTrackColor = Color.White.copy(alpha = .35f)))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(playerTime(position), color = Color.White, style = MaterialTheme.typography.labelSmall)
                    Spacer(Modifier.width(4.dp))
                    Text(playerTime(duration), color = Color.White.copy(alpha = .72f), style = MaterialTheme.typography.labelSmall)
                    Spacer(Modifier.weight(1f))
                    Box {
                        TextButton(onClick = { menu = if (menu == "speed") "" else "speed" }) { Text(speed.toString() + "x", color = Color.White) }
                        DropdownMenu(expanded = menu == "speed", onDismissRequest = { menu = "" }, containerColor = PanelLight) {
                            listOf(.25f, .5f, .75f, 1f, 1.25f, 1.5f, 1.75f, 2f, 3f, 4f).forEach { rate ->
                                DropdownMenuItem(text = { Text(rate.toString() + "x", color = Color.White) }, onClick = { speed = rate; runCatching { player.setRate(rate) }; menu = "" })
                            }
                        }
                    }
                    Box {
                        TextButton(onClick = { menu = if (menu == "subtitle") "" else "subtitle" }) { Icon(Icons.Default.Subtitles, null, tint = Color.White); Text("Subs", color = Color.White) }
                        DropdownMenu(expanded = menu == "subtitle", onDismissRequest = { menu = "" }, containerColor = PanelLight) {
                            DropdownMenuItem(text = { Text("Subtitles off", color = Color.White) }, onClick = { runCatching { player.setSpuTrack(-1) }; menu = "" })
                            subtitleTracks.forEach { track -> DropdownMenuItem(text = { Text(track.second, color = Color.White) }, onClick = { runCatching { player.setSpuTrack(track.first) }; menu = "" }) }
                            DropdownMenuItem(text = { Text("Load external subtitle…", color = Color.White) }, onClick = { menu = ""; subtitlePicker.launch(arrayOf("text/*", "application/octet-stream")) })
                            DropdownMenuItem(text = { Text("Subtitle delay −50 ms", color = Color.White) }, onClick = { subtitleDelayMs -= 50; runCatching { player.setSpuDelay(subtitleDelayMs * 1000L) }; menu = "" })
                            DropdownMenuItem(text = { Text("Subtitle delay +50 ms", color = Color.White) }, onClick = { subtitleDelayMs += 50; runCatching { player.setSpuDelay(subtitleDelayMs * 1000L) }; menu = "" })
                        }
                    }
                    Box {
                        TextButton(onClick = { menu = if (menu == "audio") "" else "audio" }) { Icon(Icons.Default.Audiotrack, null, tint = Color.White); Text("Audio", color = Color.White) }
                        DropdownMenu(expanded = menu == "audio", onDismissRequest = { menu = "" }, containerColor = PanelLight) {
                            audioTracks.forEach { track -> DropdownMenuItem(text = { Text(track.second, color = Color.White) }, onClick = { runCatching { player.setAudioTrack(track.first) }; menu = "" }) }
                            DropdownMenuItem(text = { Text("Audio delay −50 ms", color = Color.White) }, onClick = { audioDelayMs -= 50; runCatching { player.setAudioDelay(audioDelayMs * 1000L) }; menu = "" })
                            DropdownMenuItem(text = { Text("Audio delay +50 ms", color = Color.White) }, onClick = { audioDelayMs += 50; runCatching { player.setAudioDelay(audioDelayMs * 1000L) }; menu = "" })
                        }
                    }
                }
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center) {
                    TextButton(onClick = {
                        aspect = when (aspect) { "Default" -> "16:9"; "16:9" -> "4:3"; "4:3" -> "Fill"; "Fill" -> "Zoom"; else -> "Default" }
                        runCatching {
                            when (aspect) {
                                "Default" -> { player.setAspectRatio(null); player.setScale(0f) }
                                "16:9" -> { player.setAspectRatio("16:9"); player.setScale(0f) }
                                "4:3" -> { player.setAspectRatio("4:3"); player.setScale(0f) }
                                "Fill" -> { player.setAspectRatio(null); player.setScale(1.15f) }
                                else -> { player.setAspectRatio(null); player.setScale(1.35f) }
                            }
                        }
                    }) { Icon(Icons.Default.AspectRatio, null, tint = Color.White); Text(aspect, color = Color.White) }
                    TextButton(onClick = { pointA = player.time.coerceAtLeast(0L); pointB = -1L; message = "A point set at " + playerTime(pointA.toInt()) }) { Text(if (pointA >= 0 && pointB < 0) "A ✓" else "A", color = Color.White) }
                    TextButton(onClick = { if (pointA >= 0) { pointB = player.time.coerceAtLeast(0L); if (pointB <= pointA) { pointA = -1L; pointB = -1L; message = "Set A before B" } else message = "A–B repeat enabled" } else message = "Set point A first" }) { Text("B", color = Color.White) }
                    TextButton(onClick = { pointA = -1L; pointB = -1L; message = "A–B repeat cleared" }) { Text("Clear A–B", color = Color.White) }
                    TextButton(onClick = { repeatVideo = !repeatVideo }) { Icon(if (repeatVideo) Icons.Default.RepeatOne else Icons.Default.Repeat, null, tint = if (repeatVideo) Cyan else Color.White); Text("Loop", color = Color.White) }
                }
                Text(message, color = Muted, style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(horizontal = 6.dp))
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center) {
                    IconButton(onClick = { previous?.let(onNavigate) }, enabled = previous != null) { Icon(Icons.Default.SkipPrevious, "Previous video", tint = if (previous != null) Color.White else Muted) }
                    IconButton(onClick = { if (player.isPlaying) player.pause() else player.play() }, enabled = ready) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, if (playing) "Pause" else "Play", tint = Color.White, modifier = Modifier.size(31.dp)) }
                    IconButton(onClick = { next?.let(onNavigate) }, enabled = next != null) { Icon(Icons.Default.SkipNext, "Next video", tint = if (next != null) Color.White else Muted) }
                }
            }
        }
    }
}

'''
    s = s.replace(marker, component + marker, 1)

if 'private fun VlcVideoPlayerPanel(' not in s or 'org.videolan.android:libvlc-all:3.6.5' not in gradle.read_text():
    raise SystemExit("VLC player patch verification failed")
source.write_text(s)
print("Added VLC-powered playback and upgraded app to v1.6.")
