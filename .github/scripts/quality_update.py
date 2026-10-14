from pathlib import Path
p=Path("native-project/app/src/main/java/com/velvetfiles/app/MainActivity.kt")
s=p.read_text()
def rep(a,b,label):
 global s
 if b in s:return
 if a not in s:raise SystemExit("Missing anchor: "+label)
 s=s.replace(a,b,1)

# Brightness/volume HUD clears on release and its timeout resets as the value changes.
s=s.replace('LaunchedEffect(gestureMeter) { if (gestureMeter.isNotEmpty()) { delay(1100); gestureMeter = "" } }','LaunchedEffect(gestureMeter, gesturePercent) { if (gestureMeter.isNotEmpty()) { delay(850); gestureMeter = "" } }')
s=s.replace('LaunchedEffect(gestureMeter, gestureMeterPercent) {\n        if (gestureMeter.isNotEmpty()) { delay(1150); gestureMeter = "" }\n    }','LaunchedEffect(gestureMeter, gestureMeterPercent) {\n        if (gestureMeter.isNotEmpty()) { delay(850); gestureMeter = "" }\n    }')
s=s.replace('detectDragGestures(onDragStart = { startX = it.x; accumulatedY = 0f; startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) }, onDrag = { change, drag ->','detectDragGestures(onDragStart = { startX = it.x; accumulatedY = 0f; startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) }, onDragEnd = { gestureMeter = "" }, onDragCancel = { gestureMeter = "" }, onDrag = { change, drag ->')
s=s.replace('detectDragGestures(onDragStart = { startX = it.x; accumulatedY = 0f; startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) }, onDragEnd = {}, onDrag = { change, drag ->','detectDragGestures(onDragStart = { startX = it.x; accumulatedY = 0f; startingVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC) }, onDragEnd = { gestureMeter = "" }, onDragCancel = { gestureMeter = "" }, onDrag = { change, drag ->')

# Video playback stops the background audio service.
rep('''    fun openEntry(entry: FileEntry) {
        if (entry.directory) {
            goBrowse(entry.file)
        } else if (isVideoFile(entry.file) || isAudioFile(entry.file)) {''','''    fun openEntry(entry: FileEntry) {
        if (entry.directory) {
            goBrowse(entry.file)
        } else if (isVideoFile(entry.file) || isAudioFile(entry.file)) {
            if (isVideoFile(entry.file)) {
                miniAudioPlaying = false
                ContextCompat.startForegroundService(context, Intent(context, VelvetAudioService::class.java).setAction(VelvetAudioService.ACTION_STOP))
            }''',"exclusive playback")
s=s.replace('prefs.getBoolean("motion_effects", true)','prefs.getBoolean("motion_effects", false)')
s=s.replace('Column(modifier.fillMaxSize().liquidBackdrop(animate = true).padding(horizontal = 14.dp))','Column(modifier.fillMaxSize().liquidBackdrop(animate = false).padding(horizontal = 14.dp))')
s=s.replace('.animateContentSize(spring(stiffness = 500f))) {',') {')

# Extra themes.
needle='    ThemePreset("Champagne Titanium", Color(0xFF100D08), Color(0xFF211B12), Color(0xFF302719), Color(0xB83A3020), Color(0xFFFFD58A), Color(0xFFE8E7E1), Color(0xFFD2C6AB), Color(0x665A4A2D))'
if 'ThemePreset("Ocean Depth"' not in s:
 rep(needle,needle+''',
    ThemePreset("Ocean Depth", Color(0xFF04101D), Color(0xFF0B2033), Color(0xFF14344D), Color(0xB81C4260), Color(0xFF48C7FF), Color(0xFF4FFFC3), Color(0xFFB0C9DD), Color(0x5551A1C7)),
    ThemePreset("Solar Flare", Color(0xFF170A04), Color(0xFF291307), Color(0xFF3C1E0B), Color(0xB848240D), Color(0xFFFF8B38), Color(0xFFFFD35A), Color(0xFFE2C2A9), Color(0x665D351B)),
    ThemePreset("Lavender Dream", Color(0xFF100B1D), Color(0xFF1D1630), Color(0xFF2A2145), Color(0xB8322750), Color(0xFFB8A1FF), Color(0xFFFFA7E8), Color(0xFFC8BDDE), Color(0x6653447D)),
    ThemePreset("Paper Light", Color(0xFFF1F3F7), Color(0xFFE2E7EF), Color(0xFFD5DCE7), Color(0xC9FFFFFF), Color(0xFF4058A8), Color(0xFF008F99), Color(0xFF4B5565), Color(0x66596A88))''',"themes")

# Icon styles visibly alter all file classes, not only audio/video/image files.
a=s.index('private fun fileIcon(entry: FileEntry) = when {'); b=s.index('\n\n\nprivate fun compareNaturalNames',a)
s=s[:a]+'''private fun fileIcon(entry: FileEntry) = when (FileIconStyle.value) {
    "Minimal Mono" -> when { entry.directory -> Icons.Default.FolderOpen; isAudioFile(entry.file) -> Icons.Default.Audiotrack; isVideoFile(entry.file) -> Icons.Default.Movie; isImageFile(entry.file) -> Icons.Default.Photo; entry.file.extension.equals("zip", true) -> Icons.Default.FolderZip; entry.file.extension.equals("pdf", true) -> Icons.Default.PictureAsPdf; else -> Icons.Default.InsertDriveFile }
    "Classic" -> when { entry.directory -> Icons.Default.Folder; isAudioFile(entry.file) -> Icons.Default.LibraryMusic; isVideoFile(entry.file) -> Icons.Default.VideoLibrary; isImageFile(entry.file) -> Icons.Default.Collections; entry.file.extension.equals("zip", true) -> Icons.Default.Archive; entry.file.extension.equals("pdf", true) -> Icons.Default.PictureAsPdf; else -> Icons.Default.Description }
    "Pastel" -> when { entry.directory -> Icons.Default.FolderSpecial; isAudioFile(entry.file) -> Icons.Default.Headphones; isVideoFile(entry.file) -> Icons.Default.SmartDisplay; isImageFile(entry.file) -> Icons.Default.Palette; entry.file.extension.equals("zip", true) -> Icons.Default.Inventory2; entry.file.extension.equals("pdf", true) -> Icons.Default.MenuBook; else -> Icons.Default.Draft }
    "Bold" -> when { entry.directory -> Icons.Default.FolderCopy; isAudioFile(entry.file) -> Icons.Default.GraphicEq; isVideoFile(entry.file) -> Icons.Default.PlayCircleFilled; isImageFile(entry.file) -> Icons.Default.Image; entry.file.extension.equals("zip", true) -> Icons.Default.FolderZip; entry.file.extension.equals("pdf", true) -> Icons.Default.PictureAsPdf; else -> Icons.Default.InsertDriveFile }
    else -> when { entry.directory -> Icons.Default.FolderSpecial; isAudioFile(entry.file) -> Icons.Default.MusicNote; isVideoFile(entry.file) -> Icons.Default.PlayCircle; isImageFile(entry.file) -> Icons.Default.Image; entry.file.extension.equals("zip", true) -> Icons.Default.FolderZip; entry.file.extension.equals("pdf", true) -> Icons.Default.PictureAsPdf; else -> Icons.Default.InsertDriveFile }
}''' + s[b:]
s=s.replace('listOf("Neon Glass", "Minimal Mono", "Classic")','listOf("Neon Glass", "Minimal Mono", "Classic", "Pastel", "Bold")')

# Persistent whole-interface mode changes shared glass surfaces and backgrounds.
if 'private val UiStyleState' not in s:
 rep('private val FileIconStyle = mutableStateOf("Neon Glass")','private val FileIconStyle = mutableStateOf("Neon Glass")\nprivate val UiStyleState = mutableStateOf("Liquid Glass")','global style state')
rep('    var iconStyle by remember { mutableStateOf(prefs.getString("icon_style", "Neon Glass") ?: "Neon Glass") }','    var iconStyle by remember { mutableStateOf(prefs.getString("icon_style", "Neon Glass") ?: "Neon Glass") }\n    var uiStyle by remember { mutableStateOf(prefs.getString("ui_style", "Liquid Glass") ?: "Liquid Glass") }','UI style preference')
rep('    LaunchedEffect(iconStyle) { FileIconStyle.value = iconStyle }','    LaunchedEffect(iconStyle) { FileIconStyle.value = iconStyle }\n    LaunchedEffect(uiStyle) { UiStyleState.value = uiStyle }','UI style sync')
rep('''                    currentTheme = themeName,
                    onThemeSelected = { chooseTheme(it) },
                    compactRows = compact,''','''                    currentTheme = themeName,
                    onThemeSelected = { chooseTheme(it) },
                    uiStyle = uiStyle,
                    onUiStyle = { value -> uiStyle = value; prefs.edit().putString("ui_style", value).apply() },
                    compactRows = compact,''','settings callback')
rep('''private fun SettingsScreen(
    currentTheme: String,
    onThemeSelected: (ThemePreset) -> Unit,
    compactRows: Boolean,''','''private fun SettingsScreen(
    currentTheme: String,
    onThemeSelected: (ThemePreset) -> Unit,
    uiStyle: String,
    onUiStyle: (String) -> Unit,
    compactRows: Boolean,''','settings arguments')
rep('''            Text("File icon style", color = Color.White, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.fillMaxWidth()) {
                listOf("Neon Glass", "Minimal Mono", "Classic", "Pastel", "Bold").forEach { style ->
                    FilterChip(selected = iconStyle == style, onClick = { onIconStyle(style) }, label = { Text(style, maxLines = 1) }, modifier = Modifier.weight(1f))
                }
            }''','''            Text("Whole interface style", color = Color.White, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
            listOf("Liquid Glass", "Flat", "Minimal").forEach { style ->
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(style, color = Color.White, modifier = Modifier.weight(1f))
                    RadioButton(selected = uiStyle == style, onClick = { onUiStyle(style) })
                }
            }
            Text("File icon style", color = Color.White, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
            listOf("Neon Glass", "Minimal Mono", "Classic", "Pastel", "Bold").chunked(3).forEach { rowStyles ->
                Row(horizontalArrangement = Arrangement.spacedBy(5.dp), modifier = Modifier.fillMaxWidth()) {
                    rowStyles.forEach { style -> FilterChip(selected = iconStyle == style, onClick = { onIconStyle(style) }, label = { Text(style, maxLines = 1) }, modifier = Modifier.weight(1f)) }
                    if (rowStyles.size < 3) Spacer(Modifier.weight((3 - rowStyles.size).toFloat()))
                }
            }''','settings selectors')
rep('''    return this.shadow(12.dp, shape, clip = false).clip(shape)
        .background(Brush.linearGradient(listOf(Color.White.copy(alpha = .115f * strength), Glass.copy(alpha = .52f * strength), Panel.copy(alpha = .46f * strength), PanelLight.copy(alpha = .38f * strength)), Offset(0f, 0f), Offset(900f, 900f)))''','''    if (UiStyleState.value == "Minimal") return this.clip(shape).background(Panel).border(1.dp, Border, shape)
    if (UiStyleState.value == "Flat") return this.clip(shape).background(Panel).border(1.dp, Border.copy(alpha = .8f), shape)
    return this.shadow(12.dp, shape, clip = false).clip(shape)
        .background(Brush.linearGradient(listOf(Color.White.copy(alpha = .115f * strength), Glass.copy(alpha = .52f * strength), Panel.copy(alpha = .46f * strength), PanelLight.copy(alpha = .38f * strength)), Offset(0f, 0f), Offset(900f, 900f)))''','apply UI style')
s=s.replace('drawRect(Ink)\n            val radius = size.minDimension * .88f','drawRect(Ink)\n            if (UiStyleState.value != "Liquid Glass") return@drawBehind\n            val radius = size.minDimension * .88f')

# Built-in ZIP contents listing and safe extraction to the containing folder.
if 'import java.util.zip.ZipFile' not in s: rep('import java.io.File\n','import java.io.File\nimport java.util.zip.ZipFile\n','ZIP import')
if 'private fun extractZipSafely(' not in s:
 rep('private fun openFile(context: Context, file: File) {','''private fun extractZipSafely(zipFile: File, destination: File): Pair<Int, String?> {
    var count = 0
    return try {
        val root = destination.canonicalFile
        ZipFile(zipFile).use { zip ->
            val entries = zip.entries()
            while (entries.hasMoreElements()) {
                val entry = entries.nextElement()
                val target = File(root, entry.name).canonicalFile
                if (target.path != root.path && !target.path.startsWith(root.path + File.separator)) continue
                if (entry.isDirectory) target.mkdirs() else {
                    target.parentFile?.mkdirs()
                    zip.getInputStream(entry).use { input -> target.outputStream().use { output -> input.copyTo(output) } }
                    count++
                }
            }
        }
        count to null
    } catch (e: Exception) { count to (e.message ?: "Archive extraction failed") }
}

private fun openFile(context: Context, file: File) {''','ZIP extraction')
s=s.replace('private fun isPreviewableFile(file: File): Boolean = isImageFile(file) ||\n    file.extension.lowercase() in setOf("pdf",','private fun isPreviewableFile(file: File): Boolean = isImageFile(file) ||\n    file.extension.lowercase() in setOf("zip", "pdf",')
rep('''    val pdfMode = file.extension.equals("pdf", true)
    var page by remember(file.absolutePath) { mutableIntStateOf(0) }''','''    val pdfMode = file.extension.equals("pdf", true)
    val archiveMode = file.extension.equals("zip", true)
    var archiveEntries by remember(file.absolutePath) { mutableStateOf<List<String>>(emptyList()) }
    var archiveBusy by remember(file.absolutePath) { mutableStateOf(false) }
    var page by remember(file.absolutePath) { mutableIntStateOf(0) }''','archive state')
a=s.index('private fun FilePreviewScreen('); b=s.index('@Composable\nprivate fun VideoGestureMeter',a); block=s[a:b]
block=block.replace('''                when {
                    imageMode -> {''','''                when {
                    archiveMode -> { ZipFile(file).use { zip -> PreviewPayload(text = zip.entries().asSequence().take(3000).joinToString("\\n") { it.name }) } }
                    imageMode -> {''',1)
block=block.replace('''        bitmap = loaded.bitmap; text = loaded.text; pageCount = loaded.pageCount; error = loaded.error
        scale = 1f; rotation = 0f''','''        bitmap = loaded.bitmap; text = loaded.text; pageCount = loaded.pageCount; error = loaded.error
        if (archiveMode) archiveEntries = loaded.text.orEmpty().lineSequence().filter { it.isNotBlank() }.take(3000).toList()
        scale = 1f; rotation = 0f''',1)
block=block.replace('''            text != null -> androidx.compose.foundation.text.selection.SelectionContainer {''','''            archiveMode -> Column(Modifier.weight(1f).fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Text("ZIP archive contents", color = Color.White, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                    Button(enabled = !archiveBusy, onClick = {
                        archiveBusy = true
                        scope.launch {
                            val result = withContext(Dispatchers.IO) { extractZipSafely(file, file.parentFile ?: File(RootStorage.absolutePath)) }
                            archiveBusy = false
                            Toast.makeText(context, if (result.second != null) "Extract failed" else "Extracted " + result.first + " files", Toast.LENGTH_LONG).show()
                        }
                    }) { Text(if (archiveBusy) "Extracting…" else "Extract all") }
                }
                LazyColumn(Modifier.weight(1f).fillMaxWidth()) {
                    items(archiveEntries) { name ->
                        Row(Modifier.fillMaxWidth().padding(vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(if (name.endsWith("/")) Icons.Default.Folder else Icons.Default.InsertDriveFile, null, tint = Purple)
                            Spacer(Modifier.width(10.dp))
                            Text(name, color = Color.White, style = MaterialTheme.typography.bodySmall)
                        }
                        HorizontalDivider(color = Border.copy(alpha = .4f))
                    }
                }
            }
            text != null -> androidx.compose.foundation.text.selection.SelectionContainer {''',1)
s=s[:a]+block+s[b:]
rep('''        context.startActivity(Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, mimeType(file) ?: "*/*")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        })''','''        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, mimeType(file) ?: "*/*")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Open file with"))''','open with chooser')

g=Path("native-project/app/build.gradle.kts")
v=g.read_text().replace('versionCode = 8','versionCode = 9').replace('versionName = "1.7"','versionName = "1.8"')
if 'versionName = "1.8"' not in v: raise SystemExit("Expected v1.7 source before version bump")
g.write_text(v)
for x in ['LaunchedEffect(gestureMeter, gesturePercent)','ThemePreset("Ocean Depth"','Whole interface style','private fun extractZipSafely(','archiveMode -> Column','ACTION_STOP','UiStyleState.value == "Minimal"']:
 if x not in s: raise SystemExit("Verification failed: "+x)
p.write_text(s)
print("Applied Velvet Files v1.8 refinements.")
