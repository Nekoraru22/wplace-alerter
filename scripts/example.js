// Coordenadas globales (tile*1000 en Zoom 11)
function pixelsToLatLng(x, y) {
    return data.ctx.crosshair.gm.pixelsToLatLon(x, y, 11);
}

function moveTo(x, y) {
    const [lat, lng] = pixelsToLatLng(x, y);
    data.ctx.map.flyTo({
        center: { lat, lng },
        zoom: 14
    })
}

// Command to view chunks
data.ctx.map.showTileBoundaries = true;

// Go to art
moveTo(1611*1000 + 343, 875*1000 + 878)

const charges = Math.trunc(data.user.user.charges);
console.log("Charges:", charges);


// ============================================================ //
function moveTo(x, y) {
    const [lat, lng] = pixelsToLatLng(x, y);
    data.ctx.map.flyTo({
        center: { lat, lng },
        zoom: 14
    })
}
data.ctx.map.showTileBoundaries = true;
moveTo(1611*1000 + 343, 875*1000 + 878)
const charges = Math.trunc(data.user.user.charges);

// 234/71985
o.set("t=(1611,875);p=(313,795);s=0", {
    "color": { "r": 0, "g": 0, "b": 0, "a": 255 },
    "tile": [1611, 875],
    "pixel": [313, 795],
    "season": 0,
    "colorIdx": 1
});
// 235/71985
o.set("t=(1611,875);p=(314,795);s=0", {
    "color": { "r": 60, "g": 60, "b": 60, "a": 255 },
    "tile": [1611, 875],
    "pixel": [314, 795],
    "season": 0,
    "colorIdx": 2
});
// 236/71985
o.set("t=(1611,875);p=(315,795);s=0", {
    "color": { "r": 0, "g": 0, "b": 0, "a": 255 },
    "tile": [1611, 875],
    "pixel": [315, 795],
    "season": 0,
    "colorIdx": 1
});
// 237/71985
o.set("t=(1611,875);p=(316,795);s=0", {
    "color": { "r": 60, "g": 60, "b": 60, "a": 255 },
    "tile": [1611, 875],
    "pixel": [316, 795],
    "season": 0,
    "colorIdx": 2
});
// 238/71985
o.set("t=(1611,875);p=(317,795);s=0", {
    "color": { "r": 60, "g": 60, "b": 60, "a": 255 },
    "tile": [1611, 875],
    "pixel": [317, 795],
    "season": 0,
    "colorIdx": 2
});
// 239/71985
o.set("t=(1611,875);p=(318,795);s=0", {
    "color": { "r": 0, "g": 0, "b": 0, "a": 255 },
    "tile": [1611, 875],
    "pixel": [318, 795],
    "season": 0,
    "colorIdx": 1
});

document.querySelector('button.btn-lg.relative').__click();

// Copiar los resntantes al portapapeles
const text = "Example text to appear on clipboard";
navigator.clipboard.writeText(text).then(function() {
  console.log('Async: Copying to clipboard was successful!');
}, function(err) {
  console.error('Async: Could not copy text: ', err);
});