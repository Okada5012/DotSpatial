# -*- coding: utf-8 -*-
"""
遠軽町 避難施設(hinan.csv)を QGIS の「ハザードマップ」グループに追加する。
QGIS の Python コンソール(プラグイン > Python コンソール)で
「エディタを表示」→ このファイルを開く → 実行 で使用。

- 元の hinan.csv は変更しない。EngaruHazardGISData\hinan.gpkg を作成して読み込む
- アイコンは EngaruHazardGISData\img\ に SVG として書き出す（防災マップ HTML と同一図形）
- 分類は防災マップ HTML と同じ:
    指定避難所      : 指定避難所列 == '○'
    指定緊急避難場所: 指定緊急避難場所列 == '○'
    福祉避難所      : 福祉避難所列 が空でない
- CSV を更新したらこのスクリプトを再実行すると、同名レイヤを入れ替える
"""
import csv, os
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsField, QgsFields, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext,
    QgsVectorFileWriter, QgsSvgMarkerSymbolLayer, QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsUnitTypes,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtCore import QVariant, QPointF
from qgis.PyQt.QtGui import QColor, QFont

GROUP_NAME = 'ハザードマップ'
# CSV の場所（プロジェクトと同じフォルダ基準。違う場合はここを書き換える）
BASE = os.path.join(QgsProject.instance().homePath(), '地図情報', 'EngaruHazardGISData')
CSV_PATH = os.path.join(BASE, 'hinan.csv')
IMG_DIR = os.path.join(BASE, 'img')
GPKG = os.path.join(BASE, 'hinan.gpkg')

SVGS = {'kennyo': '<svg width="24" height="24" viewBox="0 0 68.4 68.4" xmlns="http://www.w3.org/2000/svg"><rect width="68.4" height="68.4" fill="white"/><path fill="#02a556" d="M68.4,0v68.4H0V0h68.4ZM62.8,67.2V23.8L34.23,5.59,6,23.8v43.4h14v-20.4c4.79.93,5.29-1.44,8-4.4l2.78,6.6-8.77,18.2c1.87-.22,4.35.75,5.6-.99l7.2-15.4.79,4.6c-.16,1.1-.14,5.4,1.4,5.4h14.2c-.43-1.26-1.47-3.41-2.78-3.82-1.75-.55-7.93.49-8.36-.84.72-6.28-1.72-11.02-4.05-16.54l3.93.06c1.11,1.83,2.5,7.11,5.26,5.74l.74-.89c.24-.88-2.3-5.48-2.98-6.48-.41-.61-.76-1.41-1.46-1.74-1.18-.55-11.55-.48-13.04-.03-3.42,1.04-4.2,7.8-8.46,6.94v-18.8h28.4v31.4c0,.16,1.94,1.34,2.4,2,.26.37,1.6,3.3,1.6,3.6l-4,.2v5.6h14.4ZM27.1,28.5c-4.44,1.17-2.64,8.57,2.52,6.92,3.84-1.23,2.61-8.27-2.52-6.92Z"/></svg>', 'kinkyuu': '<svg width="28" height="28" viewBox="-5 -5 73 70" xmlns="http://www.w3.org/2000/svg"><circle cx="31.6" cy="30" r="34" fill="white"/><path fill="#02a556" d="M27.23,47.02h5.88c.08,0,1.4-.37,1.56-.44,2.17-1,4.42-7.38,5.6-9.53,6.1,1.17,13.12,5.13,11.61,12.48-1.88,9.12-21.8,10.62-29.02,10.25-7.51-.39-27.02-3.97-22.05-15.57,3.65-8.52,23.15-9.84,31.06-8.94.22,0,.59.2.63.38.13.65-5.1,9.71-5.25,11.37Z"/><path fill="#02a556" d="M44.98,13.27c.94,3.06,3.42,6.46,4.14,9.49.76,3.21.46,7.2.86,10.51h9.12c2.11,0,3.85,2.91,4.12,4.75h-16.62c-.11,0-.74-.47-.88-.62-1.55-1.69-.82-8.47-1.37-10.88l-8.33,16.67c-.49.68-1.24,2.33-2.17,2.33h-4.62c2.65-6.4,5.98-12.51,8.79-18.83.24-.53,1.02-2.05,1.1-2.41.22-1.01-2.69-6.42-3.27-7.75-1.62,1.51-2.63,4.87-5.02,5.22-1.4.2-6.93-.24-8.36-.6-1.98-.49-1.67-3.54.4-3.86,1.31-.21,6.47.28,7.06-.07,1.5-2.19,4.07-6.9,6.56-7.82,1.88-.69,10.01-.56,12.37-.38,1.17.09,2.6.25,3.51.99.83.67,4.42,6.93,4.57,7.95.3,2.13-1.93,3.33-3.56,1.54-.73-.8-3.4-6.24-3.76-6.24h-4.62Z"/><path fill="#02a556" d="M35.42.08c5.37-.9,7.16,6.22,2.73,8.23-3.33,1.51-6.71-1.34-6.11-4.86.25-1.5,1.88-3.12,3.37-3.37Z"/></svg>', 'fukushi': '<svg width="24" height="24" viewBox="0 0 68.4 68.4" xmlns="http://www.w3.org/2000/svg"><path fill="#1bc1ce" d="M68.4,0v68.4H0V0h68.4ZM62.8,67.2V23.8L34.23,5.59,6,23.8v43.4h14v-20.4c4.79.93,5.29-1.44,8-4.4l2.78,6.6-8.77,18.2c1.87-.22,4.35.75,5.6-.99l7.2-15.4.79,4.6c-.16,1.1-.14,5.4,1.4,5.4h14.2c-.43-1.26-1.47-3.41-2.78-3.82-1.75-.55-7.93.49-8.36-.84.72-6.28-1.72-11.02-4.05-16.54l3.93.06c1.11,1.83,2.5,7.11,5.26,5.74l.74-.89c.24-.88-2.3-5.48-2.98-6.48-.41-.61-.76-1.41-1.46-1.74-1.18-.55-11.55-.48-13.04-.03-3.42,1.04-4.2,7.8-8.46,6.94v-18.8h28.4v31.4c0,.16,1.94,1.34,2.4,2,.26.37,1.6,3.3,1.6,3.6l-4,.2v5.6h14.4ZM27.1,28.5c-4.44,1.17-2.64,8.57,2.52,6.92,3.84-1.23,2.61-8.27-2.52-6.92Z"/></svg>'}

# (レイヤ名, キー, フィルタ式, SVG, サイズmm) 上のものほど地図上で手前
LAYERS = [
    ('福祉避難所',         'fukushi', '"fukushi" IS NOT NULL AND "fukushi" <> \'\'', 6.0),
    ('指定避難所',         'kennyo',  '"kennyo" = \'○\'',                           6.0),
    ('指定緊急避難場所',   'kinkyuu', '"kinkyuu" = \'○\'',                          7.0),
]

# ---- 1. SVG を書き出す ----
os.makedirs(IMG_DIR, exist_ok=True)
svg_path = {}
for key, text in SVGS.items():
    p = os.path.join(IMG_DIR, 'hinan_%s.svg' % key)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    svg_path[key] = p

# ---- 2. CSV を読み GeoPackage にする（列位置固定：HTML と同じ） ----
# 0:no 1:name 2:lat 3:lng 4:kennyo 5:kinkyuu 6:fukushi 7:address 8:tel
# 9:flood 10:slope 11:quake 12:fire 13:target
with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.reader(f))[1:]

fields = QgsFields()
for n in ['no','name','kennyo','kinkyuu','fukushi','address','tel','flood','slope','quake','fire','target']:
    fields.append(QgsField(n, QVariant.String))
fields.append(QgsField('lat', QVariant.Double))
fields.append(QgsField('lng', QVariant.Double))

crs = QgsCoordinateReferenceSystem('EPSG:4326')
tmp = QgsVectorLayer('Point?crs=EPSG:4326', 'hinan', 'memory')
pr = tmp.dataProvider()
pr.addAttributes(fields.toList()); tmp.updateFields()
feats = []; skipped = []
for r in rows:
    g = lambda i: (r[i].strip() if i < len(r) else '')
    if not g(0):
        continue
    try:
        lat, lng = float(g(2)), float(g(3))
    except ValueError:
        skipped.append(g(0)); continue
    ft = QgsFeature(tmp.fields())
    ft.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lng, lat)))
    ft.setAttributes([g(0), g(1), g(4), g(5), g(6), g(7), g(8), g(9), g(10), g(11), g(12), g(13), lat, lng])
    feats.append(ft)
pr.addFeatures(feats); tmp.updateExtents()

# 既存レイヤが gpkg を掴んでいると上書きできないので先に外す
proj = QgsProject.instance()
for name, *_ in LAYERS:
    for old in proj.mapLayersByName(name):
        proj.removeMapLayer(old.id())

opts = QgsVectorFileWriter.SaveVectorOptions()
opts.driverName = 'GPKG'; opts.layerName = 'hinan'; opts.fileEncoding = 'UTF-8'
opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
res = QgsVectorFileWriter.writeAsVectorFormatV3(tmp, GPKG, QgsCoordinateTransformContext(), opts)
if res[0] != QgsVectorFileWriter.NoError:
    raise RuntimeError('GeoPackage 書き出し失敗: %s' % (res,))

# ---- 3. グループ取得 ----
root = proj.layerTreeRoot()
group = root.findGroup(GROUP_NAME)
if group is None:
    group = root.insertGroup(0, GROUP_NAME)
    print('グループ「%s」が無かったので新規作成しました' % GROUP_NAME)

# ---- 4. レイヤ作成・スタイル ----
made = []
for name, key, expr, size in LAYERS:
    lyr = QgsVectorLayer('%s|layername=hinan' % GPKG, name, 'ogr')
    if not lyr.isValid():
        raise RuntimeError('レイヤ読込失敗: ' + name)
    lyr.setSubsetString(expr)

    sl = QgsSvgMarkerSymbolLayer(svg_path[key])
    sl.setSize(size); sl.setSizeUnit(QgsUnitTypes.RenderMillimeters)
    sl.setOffset(QPointF(0, -size / 2))  # 下端を地点に合わせる
    sl.setOffsetUnit(QgsUnitTypes.RenderMillimeters)
    lyr.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol([sl])))

    made.append(lyr)

# 施設名ラベルは重複を避けるため「指定避難所」レイヤにだけ付ける
lab = QgsPalLayerSettings()
lab.fieldName = 'name'
fmt = QgsTextFormat(); fmt.setFont(QFont('Meiryo')); fmt.setSize(9); fmt.setColor(QColor('#1a1a1a'))
buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(1.0); buf.setColor(QColor('white'))
fmt.setBuffer(buf); lab.setFormat(fmt)
lab.placement = QgsPalLayerSettings.OverPoint
lab.xOffset = 0; lab.yOffset = 1.5
lab.scaleVisibility = True; lab.maximumScale = 0; lab.minimumScale = 15000
for lyr in made:
    if lyr.name() == '指定避難所':
        lyr.setLabeling(QgsVectorLayerSimpleLabeling(lab)); lyr.setLabelsEnabled(True)

for lyr in made:
    proj.addMapLayer(lyr, False)
    group.addLayer(lyr)

# グループ内の並び：福祉 > 指定避難所 > 指定緊急避難場所（LAYERS の順）は addLayer 順で確保済み
group.setExpanded(True)
print('完了: %d 施設 / スキップ(座標なし) %s' % (len(feats), skipped or 'なし'))
print('GeoPackage:', GPKG)
