/**
 * Decompress a URL by replacing a numeric prefix index with the full URL prefix.
 *
 * Compressed format: "idx~suffix" → meta.u[idx] + suffix
 * Tildes in the suffix (e.g. YouTube labels) are preserved by rejoining.
 * Returns the original string if no prefix index is found, or null if empty.
 *
 * @param {Object} meta  - The shared meta block containing a `u` (url_prefixes) array.
 * @param {string} str   - The compressed URL string, or falsy for null.
 * @returns {string|null}
 */
function decompressUrl(meta, str) {
    if (!str) return null;
    if (!str.includes('~')) return str;

    var parts = str.split('~');
    var idx = parseInt(parts[0], 10);
    if (!isNaN(idx) && meta.u && meta.u[idx]) {
        return meta.u[idx] + parts.slice(1).join('~');
    }
    return str;
}
