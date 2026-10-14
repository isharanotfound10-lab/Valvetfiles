from pathlib import Path

p = Path("native-project/app/src/main/java/com/velvetfiles/app/MainActivity.kt")
s = p.read_text()

def once(old, new, label):
    global s
    if new and new in s:
        return
    if old not in s:
        raise SystemExit("Could not locate " + label + "; refusing to apply partial patch")
    s = s.replace(old, new, 1)

# Keep both browsing layouts alive while the player temporarily replaces the file list.
once("import androidx.compose.foundation.lazy.LazyColumn\n",
     "import androidx.compose.foundation.lazy.LazyColumn\nimport androidx.compose.foundation.lazy.rememberLazyListState\nimport androidx.compose.foundation.lazy.grid.rememberLazyGridState\nimport androidx.compose.foundation.gestures.detectVerticalDragGestures\nimport androidx.compose.ui.input.pointer.pointerInput\n",
     "lazy-list imports")
once("import androidx.compose.ui.text.font.FontWeight\n",
     "import androidx.compose.ui.text.font.FontWeight\nimport androidx.compose.ui.text.font.FontFamily\nimport androidx.compose.ui.text.TextStyle\nimport androidx.compose.foundation.text.BasicTextField\n",
     "code-editor imports")
once('    var refreshKey by remember { mutableIntStateOf(0) }\n',
     '    var refreshKey by remember { mutableIntStateOf(0) }\n    val browseListState = rememberLazyListState()\n    val browseGridState = rememberLazyGridState()\n    var miniAudioArtwork by remember { mutableStateOf<Bitmap?>(null) }\n    var miniAudioCollapsed by remember { mutableStateOf(false) }\n',
     "persistent browsing state")
once('    LaunchedEffect(themeName, customAccentArgb) {\n',
     '''    LaunchedEffect(miniAudioPath) {
        miniAudioCollapsed = false
        miniAudioArtwork = withContext(Dispatchers.IO) {
            val path = miniAudioPath
            if (path.isNullOrBlank() || !File(path).isFile) null else {
                val retriever = MediaMetadataRetriever()
                try {
                    retriever.setDataSource(path)
                    val bytes = retriever.embeddedPicture
                    if (bytes == null) null else {
                        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
                        var sample = 1
                        while (bounds.outWidth / sample > 640 || bounds.outHeight / sample > 640) sample *= 2
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, BitmapFactory.Options().apply { inSampleSize = sample })
                    }
                } catch (_: Exception) { null } finally { try { retriever.release() } catch (_: Exception) {} }
            }
        }
    }
    LaunchedEffect(currentFolder.absolutePath) {
        browseListState.scrollToItem(0)
        browseGridState.scrollToItem(0)
    }
    LaunchedEffect(themeName, customAccentArgb) {
''',
     "artwork loading and folder-only scroll reset")

# Accept a null path from the audio service as a real stop event, not stale metadata.
once('                if (!path.isNullOrBlank()) miniAudioPath = path\n',
     '                if (intent.hasExtra(VelvetAudioService.EXTRA_PATH)) miniAudioPath = path?.takeIf { it.isNotBlank() }\n',
     "audio stop-state receiver")
once('if (!miniAudioPath.isNullOrBlank() && File(miniAudioPath!!).isFile) {',
     'if (!miniAudioPath.isNullOrBlank() && File(miniAudioPath!!).isFile) {',
     "mini-player visibility anchor")

once('if (!miniAudioPath.isNullOrBlank() && File(miniAudioPath!!).isFile) {',
     'if (miniAudioPlaying && !miniAudioPath.isNullOrBlank() && File(miniAudioPath!!).isFile) {',
     "hide mini-player unless audio is actively playing")

# Add a swipe-down collapse affordance to the mini audio player.
if "miniAudioCollapsed" not in s[s.index("if (miniAudioPlaying && !miniAudioPath"):s.index("LazyVerticalGrid", s.index("if (miniAudioPlaying && !miniAudioPath"))]:
    player_start = s.index("if (miniAudioPlaying && !miniAudioPath.isNullOrBlank() && File(miniAudioPath!!).isFile) {")
    panel_start = s.index("GlassPanel {", player_start)
    # Find the end of this GlassPanel content block with a simple Kotlin brace scan.
    panel_open = s.index("{", panel_start + len("GlassPanel "))
    depth = 0
    in_string = False
    quote = ""
    escaped = False
    panel_end = None
    for i in range(panel_open, len(s)):
        ch = s[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                panel_end = i
                break
    if panel_end is None:
        raise SystemExit("Could not locate mini-player panel boundary")
    compact_panel = """if (miniAudioCollapsed) {
                GlassPanel(modifier = if (motionEnabled) Modifier.animateContentSize() else Modifier) {
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.MusicNote, null, tint = Cyan)
                        Spacer(Modifier.width(10.dp))
                        Text(miniAudioTitle, color = Color.White, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                        IconButton(onClick = { miniAudioCollapsed = false }) { Icon(Icons.Default.ExpandLess, "Expand audio player", tint = Purple) }
                    }
                }
            } else {
                """
    s = s[:panel_start] + compact_panel + s[panel_start:]
    panel_start = s.index("GlassPanel {", player_start)
    s = s[:panel_start] + s[panel_start:].replace("GlassPanel {", """GlassPanel(modifier = Modifier.pointerInput(motionEnabled) {
                    var downwardDrag = 0f
                    detectVerticalDragGestures(
                        onDragStart = { downwardDrag = 0f },
                        onVerticalDrag = { change, dragAmount ->
                            downwardDrag += dragAmount
                            if (downwardDrag > 36f) {
                                miniAudioCollapsed = true
                                change.consume()
                            }
                        }
                    )
                }.then(if (motionEnabled) Modifier.animateContentSize() else Modifier)) {""", 1)
    panel_start = s.index("GlassPanel(modifier = Modifier.pointerInput(motionEnabled)", player_start)
    # Locate the opening brace of the GlassPanel content lambda, after the modifier argument.
    panel_open = s.index(")) {", panel_start) + 3
    depth = 0
    in_string = False
    quote = ""
    escaped = False
    panel_end = None
    for i in range(panel_open, len(s)):
        ch = s[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                panel_end = i
                break
    if panel_end is None:
        raise SystemExit("Could not close swipe-enabled mini-player")
    s = s[:panel_end + 1] + "\n            }" + s[panel_end + 1:]

old_art = 'Box(Modifier.size(42.dp).clip(RoundedCornerShape(12.dp)).background(Brush.radialGradient(listOf(Purple.copy(alpha = .65f), Glass, Ink))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = Cyan) }'
new_art = '''Box(Modifier.size(46.dp).clip(RoundedCornerShape(12.dp)).background(Brush.radialGradient(listOf(Purple.copy(alpha = .65f), Glass, Ink))), contentAlignment = Alignment.Center) {
                                        val cover = miniAudioArtwork
                                        if (cover != null) Image(bitmap = cover.asImageBitmap(), contentDescription = "Album artwork", modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                                        else Icon(Icons.Default.Album, null, tint = Cyan, modifier = Modifier.size(27.dp))
                                    }'''
once(old_art, new_art, "mini-player artwork thumbnail")
stop_button_old = 'IconButton(onClick = { context.stopService(Intent(context, VelvetAudioService::class.java)) }) { Icon(Icons.Default.Close, "Stop audio", tint = Muted) }'
stop_button_new = 'IconButton(onClick = { miniAudioPath = null; miniAudioTitle = "Audio player"; miniAudioPlaying = false; miniAudioArtwork = null; context.stopService(Intent(context, VelvetAudioService::class.java)) }) { Icon(Icons.Default.Close, "Stop audio and hide player", tint = Muted) }'
if stop_button_new not in s:
    if stop_button_old in s:
        s = s.replace(stop_button_old, stop_button_new, 1)
    else:
        print("Stop-button cleanup anchor differs in this player version; skipping optional mini-player rewrite.")

once('LazyVerticalGrid(columns = GridCells.Adaptive(145.dp), contentPadding = PaddingValues(top = 8.dp, bottom = 90.dp),',
     'LazyVerticalGrid(state = browseGridState, columns = GridCells.Adaptive(145.dp), contentPadding = PaddingValues(top = 8.dp, bottom = 90.dp),',
     "grid scroll state")
once('LazyColumn(verticalArrangement = Arrangement.spacedBy(FileListSpacing.floatValue.dp), contentPadding = PaddingValues(top = 8.dp, bottom = 90.dp)) {',
     'LazyColumn(state = browseListState, verticalArrangement = Arrangement.spacedBy(FileListSpacing.floatValue.dp), contentPadding = PaddingValues(top = 8.dp, bottom = 90.dp)) {',
     "list scroll state")

# Make fullscreen affect the parent layout, not only Android's system bars.
once('''    val video = isVideoFile(file)
    Column(modifier.fillMaxSize().liquidBackdrop(animate = true).padding(horizontal = 14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 7.dp)) {
''',
'''    val video = isVideoFile(file)
    var videoFullscreen by remember(file.absolutePath) { mutableStateOf(false) }
    Column(modifier.fillMaxSize().then(if (videoFullscreen) Modifier.background(Color.Black) else Modifier.liquidBackdrop(animate = true).padding(horizontal = 14.dp))) {
        if (!videoFullscreen) Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 7.dp)) {
''', "media-player fullscreen parent layout")
media_start = s.index("private fun MediaPlayerScreen(")
media_end = s.index("@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nprivate fun VlcVideoPlayerPanel(", media_start)
media_block = s[media_start:media_end]
if "            VlcVideoPlayerPanel(" in media_block:
    video_start = media_block.index("            VlcVideoPlayerPanel(")
    video_end = media_block.index("        } else {", video_start)
    video_chunk = '''            VlcVideoPlayerPanel(file, queue.filter { isVideoFile(it) }, Modifier.weight(1f).fillMaxWidth(), onNavigate, onVideoProgress, videoFullscreen, { videoFullscreen = it })
            if (!videoFullscreen) {
                Spacer(Modifier.height(8.dp))
                GlassPanel(animate = false) {
                    Text(file.name, color = Color.White, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    Text("\${file.extension.uppercase()} · \${humanSize(file.length())} · " + DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(file.lastModified())), color = Muted, style = MaterialTheme.typography.bodySmall)
                }
            }
'''
    media_block = media_block[:video_start] + video_chunk + media_block[video_end:]
    s = s[:media_start] + media_block + s[media_end:]
else:
    print("Keeping the original video-player call; skipping VLC-only fullscreen rewrite.")
once('''        Spacer(Modifier.height(8.dp))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VlcVideoPlayerPanel(''',
'''        if (!videoFullscreen) Spacer(Modifier.height(8.dp))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VlcVideoPlayerPanel(''', "fullscreen bottom spacing")
once('''    onNavigate: (File) -> Unit,
    onPosition: (String, Int, Int) -> Unit
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("file_manager_preferences", Context.MODE_PRIVATE) }
    val activity = context as? Activity
    val audioManager = remember { context.getSystemService(Context.AUDIO_SERVICE) as AudioManager }
    val libVlc = remember(file.absolutePath, context) {''',
'''    onNavigate: (File) -> Unit,
    onPosition: (String, Int, Int) -> Unit,
    fullscreen: Boolean,
    onFullscreenChanged: (Boolean) -> Unit
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("file_manager_preferences", Context.MODE_PRIVATE) }
    val activity = context as? Activity
    val audioManager = remember { context.getSystemService(Context.AUDIO_SERVICE) as AudioManager }
    val libVlc = remember(file.absolutePath, context) {''', "VLC fullscreen parameters")
vlc_start = s.index("private fun VlcVideoPlayerPanel(")
vlc_end = s.index("@Composable\nprivate fun VideoPlayerPanel(", vlc_start)
vlc_block = s[vlc_start:vlc_end]
vlc_block = vlc_block.replace('    var fullscreen by remember(file.absolutePath) { mutableStateOf(false) }\n', '', 1)
old_fullscreen_button = 'IconButton(onClick = { fullscreen = !fullscreen }) { Icon(if (fullscreen) Icons.Default.FullscreenExit else Icons.Default.Fullscreen, "Toggle fullscreen", tint = Color.White) }'
new_fullscreen_button = 'IconButton(onClick = { onFullscreenChanged(!fullscreen) }) { Icon(if (fullscreen) Icons.Default.FullscreenExit else Icons.Default.Fullscreen, "Toggle fullscreen", tint = Color.White) }'
if old_fullscreen_button not in vlc_block:
    raise SystemExit("Could not locate fullscreen button inside VLC player")
vlc_block = vlc_block.replace(old_fullscreen_button, new_fullscreen_button, 1)
s = s[:vlc_start] + vlc_block + s[vlc_end:]

# Expand preview routing so the editor can open common programming languages.
text_preview_old = 'private fun isTextPreview(file: File): Boolean = file.extension.lowercase() in setOf("txt", "md", "markdown", "json", "xml", "kt", "java", "log", "csv", "html", "htm", "css", "js", "properties", "yml", "yaml", "gradle", "sh")'
text_preview_new = 'private fun isTextPreview(file: File): Boolean = file.extension.lowercase() in setOf("txt", "md", "markdown", "json", "xml", "kt", "kts", "java", "py", "log", "csv", "html", "htm", "css", "scss", "js", "ts", "jsx", "tsx", "sql", "properties", "yml", "yaml", "toml", "ini", "gradle", "sh", "bash", "c", "h", "cpp", "hpp", "rs", "go", "php", "rb", "swift", "dart")'
if text_preview_old in s:
    s = s.replace(text_preview_old, text_preview_new, 1)
elif text_preview_new not in s:
    raise SystemExit("Could not expand code-file preview extensions")

# Turn source/config text previews into a practical native code editor.
once('''    val imageMode = isImageFile(file)
    val pdfMode = file.extension.equals("pdf", true)
    var page by remember(file.absolutePath) { mutableIntStateOf(0) }
''',
'''    val imageMode = isImageFile(file)
    val pdfMode = file.extension.equals("pdf", true)
    val codeMode = file.extension.lowercase() in setOf("kt", "kts", "java", "py", "js", "ts", "jsx", "tsx", "json", "xml", "html", "htm", "css", "scss", "sql", "sh", "bash", "yml", "yaml", "toml", "ini", "properties", "gradle", "c", "h", "cpp", "hpp", "rs", "go", "php", "rb", "swift", "dart", "md")
    var editingCode by remember(file.absolutePath) { mutableStateOf(false) }
    var editorText by remember(file.absolutePath) { mutableStateOf("") }
    var originalCode by remember(file.absolutePath) { mutableStateOf("") }
    var undoStack by remember(file.absolutePath) { mutableStateOf(listOf<String>()) }
    var redoStack by remember(file.absolutePath) { mutableStateOf(listOf<String>()) }
    var showFindReplace by remember(file.absolutePath) { mutableStateOf(false) }
    var findText by remember(file.absolutePath) { mutableStateOf("") }
    var replaceText by remember(file.absolutePath) { mutableStateOf("") }
    var page by remember(file.absolutePath) { mutableIntStateOf(0) }
''', "code editor state")
once('''        bitmap = loaded.bitmap; text = loaded.text; pageCount = loaded.pageCount; error = loaded.error
        scale = 1f; rotation = 0f
''',
'''        bitmap = loaded.bitmap; text = loaded.text; pageCount = loaded.pageCount; error = loaded.error
        if (codeMode && loaded.text != null) {
            editorText = loaded.text
            originalCode = loaded.text
            undoStack = emptyList(); redoStack = emptyList(); editingCode = false
        }
        scale = 1f; rotation = 0f
''', "initialize code editor")
once('''            IconButton(onClick = { shareFile(context, file) }) { Icon(Icons.Default.Share, "Share file", tint = Purple) }
        }
        when {
''',
'''            if (codeMode && text != null) {
                if (editingCode) {
                    IconButton(onClick = { if (undoStack.isNotEmpty()) { redoStack = redoStack + editorText; editorText = undoStack.last(); undoStack = undoStack.dropLast(1) } }, enabled = undoStack.isNotEmpty()) { Icon(Icons.Default.Undo, "Undo", tint = Purple) }
                    IconButton(onClick = { if (redoStack.isNotEmpty()) { undoStack = undoStack + editorText; editorText = redoStack.last(); redoStack = redoStack.dropLast(1) } }, enabled = redoStack.isNotEmpty()) { Icon(Icons.Default.Redo, "Redo", tint = Purple) }
                    IconButton(onClick = { showFindReplace = !showFindReplace }) { Icon(Icons.Default.FindReplace, "Find and replace", tint = Purple) }
                    TextButton(onClick = {
                        scope.launch {
                            val failure = withContext(Dispatchers.IO) { runCatching { file.writeText(editorText, Charsets.UTF_8) }.exceptionOrNull() }
                            if (failure == null) {
                                originalCode = editorText; text = editorText; editingCode = false
                                Toast.makeText(context, "Saved \${file.name}", Toast.LENGTH_SHORT).show()
                            } else Toast.makeText(context, "Save failed: \${failure.message}", Toast.LENGTH_LONG).show()
                        }
                    }) { Text("Save", color = if (editorText != originalCode) Color(0xFF9FFFD2) else Purple) }
                } else {
                    IconButton(onClick = { editorText = text.orEmpty(); originalCode = text.orEmpty(); undoStack = emptyList(); redoStack = emptyList(); editingCode = true }) { Icon(Icons.Default.Code, "Edit source code", tint = Purple) }
                }
            }
            IconButton(onClick = { shareFile(context, file) }) { Icon(Icons.Default.Share, "Share file", tint = Purple) }
        }
        if (editingCode && showFindReplace) {
            Column(Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                OutlinedTextField(value = findText, onValueChange = { findText = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("Find") })
                Row(verticalAlignment = Alignment.CenterVertically) {
                    OutlinedTextField(value = replaceText, onValueChange = { replaceText = it }, modifier = Modifier.weight(1f), singleLine = true, label = { Text("Replace with") })
                    TextButton(onClick = {
                        if (findText.isNotEmpty() && editorText.contains(findText)) {
                            undoStack = (undoStack + editorText).takeLast(100); redoStack = emptyList()
                            editorText = editorText.replace(findText, replaceText)
                        }
                    }) { Text("Replace all", color = Purple) }
                }
            }
        }
        when {
''', "editor toolbar and find/replace")
once('''            text != null -> androidx.compose.foundation.text.selection.SelectionContainer {
                Text(text!!, color = Color(0xFFEDE7F5), style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(12.dp))
            }
''',
'''            text != null && editingCode -> Column(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(Color(0xFF101019)).padding(8.dp)) {
                Row(Modifier.fillMaxWidth().padding(bottom = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(file.extension.uppercase() + " · " + editorText.count { it == '\\n' } .plus(1) + " lines", color = Cyan, style = MaterialTheme.typography.labelSmall)
                    Spacer(Modifier.weight(1f))
                    Text(if (editorText == originalCode) "Saved" else "Unsaved changes", color = if (editorText == originalCode) Muted else Color(0xFFFFD18A), style = MaterialTheme.typography.labelSmall)
                }
                Row(Modifier.weight(1f).fillMaxWidth(), verticalAlignment = Alignment.Top) {
                    Text((1..editorText.count { it == '\\n' }.plus(1)).joinToString("\\n"), color = Color(0xFF7E83A4), fontFamily = FontFamily.Monospace, style = TextStyle(fontSize = 12.sp, lineHeight = 19.sp), modifier = Modifier.width(38.dp).fillMaxHeight().verticalScroll(rememberScrollState()).padding(end = 6.dp))
                    BasicTextField(value = editorText, onValueChange = { next ->
                        if (next != editorText) { undoStack = (undoStack + editorText).takeLast(100); redoStack = emptyList(); editorText = next }
                    }, modifier = Modifier.weight(1f).fillMaxHeight().verticalScroll(rememberScrollState()), textStyle = TextStyle(color = Color(0xFFEDE7F5), fontFamily = FontFamily.Monospace, fontSize = 12.sp, lineHeight = 19.sp), cursorBrush = androidx.compose.ui.graphics.SolidColor(Cyan))
                }
            }
            text != null -> androidx.compose.foundation.text.selection.SelectionContainer {
                Text(text!!, color = Color(0xFFEDE7F5), style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(12.dp))
            }
''', "editable code pane")
# Update helper caption and confirm all key features survived transformation.
if "rememberLazyListState" not in s or "onFullscreenChanged(!fullscreen)" not in s:
    raise SystemExit("Scroll or fullscreen patch verification failed")
if "Album artwork" not in s or "Find and replace" not in s or "Replace all" not in s or "originalCode" not in s:
    raise SystemExit("Mini-player or code editor patch verification failed")
gradle = Path("native-project/app/build.gradle.kts")
g = gradle.read_text()
g = g.replace("versionCode = 7", "versionCode = 8").replace('versionName = "1.6"', 'versionName = "1.7"')
gradle.write_text(g)
if 'versionName = "1.7"' not in g:
    raise SystemExit("Version bump failed")
p.write_text(s)
print("Applied: true audio-stop visibility, embedded artwork thumbnail, folder scroll restoration, true fullscreen layout, and native code editor tools.")
