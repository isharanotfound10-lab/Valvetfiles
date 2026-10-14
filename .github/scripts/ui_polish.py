from pathlib import Path
import re

source = Path("native-project/app/src/main/java/com/velvetfiles/app/MainActivity.kt")
if not source.exists():
    raise SystemExit(f"MainActivity.kt not found: {source}")
s = source.read_text()

# Natural numeric ordering: file2 sorts before file10, while folders retain their priority.
if "private fun compareNaturalNames(" not in s:
    marker = "private fun isPendingTemporaryName(name: String): Boolean"
    if marker not in s:
        marker = "private fun listDirectory(folder: File"
    if marker not in s:
        raise SystemExit("Could not find a safe insertion point for natural sorting")
    comparator = r'''
private fun compareNaturalNames(left: String, right: String): Int {
    var i = 0
    var j = 0
    while (i < left.length && j < right.length) {
        val a = left[i]
        val b = right[j]
        if (a.isDigit() && b.isDigit()) {
            val leftStart = i
            val rightStart = j
            while (i < left.length && left[i].isDigit()) i++
            while (j < right.length && right[j].isDigit()) j++
            var leftSignificant = leftStart
            var rightSignificant = rightStart
            while (leftSignificant < i && left[leftSignificant] == '0') leftSignificant++
            while (rightSignificant < j && right[rightSignificant] == '0') rightSignificant++
            val leftDigits = i - leftSignificant
            val rightDigits = j - rightSignificant
            if (leftDigits != rightDigits) return leftDigits.compareTo(rightDigits)
            val numericCompare = left.substring(leftSignificant, i)
                .compareTo(right.substring(rightSignificant, j))
            if (numericCompare != 0) return numericCompare
            val zeroPaddingCompare = (i - leftStart).compareTo(j - rightStart)
            if (zeroPaddingCompare != 0) return zeroPaddingCompare
        } else {
            val charCompare = a.lowercaseChar().compareTo(b.lowercaseChar())
            if (charCompare != 0) return charCompare
            i++
            j++
        }
    }
    return (left.length - i).compareTo(right.length - j)
}

'''
    s = s.replace(marker, comparator + marker, 1)

s = s.replace(
    ".thenBy { it.name.lowercase() }",
    ".thenComparator { left, right -> compareNaturalNames(left.name, right.name) }"
)
s = s.replace(
    "filtered.sortedBy { it.name.lowercase() }",
    "filtered.sortedWith(Comparator { left, right -> compareNaturalNames(left.name, right.name) })"
)
s = s.replace(
    "filtered.sortedByDescending { it.name.lowercase() }",
    "filtered.sortedWith(Comparator { left, right -> compareNaturalNames(right.name, left.name) })"
)

# Keep ambient glass motion elegant rather than fast or distracting.
s = re.sub(
    r'(tween\(if \(animate\) )\d+( else 90000, easing = LinearEasing\), RepeatMode\.Restart\), label = "specularSweep")',
    r'\g<1>7800\2',
    s
)
s = re.sub(
    r'(tween\(if \(animate\) )\d+( else 90000, easing = LinearEasing\), RepeatMode\.Reverse\), label = "ambientDrift")',
    r'\g<1>16000\2',
    s
)

# Animate tile size changes as file names/metadata settle in.
tile_start = s.find("@Composable\nprivate fun FileTile(")
tile_end = s.find("@Composable\nprivate fun FileThumbnail(", tile_start)
if tile_start >= 0 and tile_end > tile_start:
    tile = s[tile_start:tile_end]
    tile = tile.replace(
        "combinedClickable(onClick = onClick, onLongClick = onLongClick)) {",
        "combinedClickable(onClick = onClick, onLongClick = onLongClick).then(if (MotionEffectsEnabled.value) Modifier.animateContentSize() else Modifier)) {"
    )
    s = s[:tile_start] + tile + s[tile_end:]

# Sanity checks make the workflow fail rather than silently produce a partial patch.
if "private fun compareNaturalNames(" not in s:
    raise SystemExit("Natural comparator was not installed")
if "Name · Z–A" in s and "filtered.sortedByDescending { it.name.lowercase() }" in s:
    raise SystemExit("Descending filename sort still uses lexical ordering")
source.write_text(s)
print("UI polish applied: natural numeric filename sorting, gentler ambient motion, and animated grid tiles.")
