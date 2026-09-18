import os
import io
import urllib.request
import urllib.parse
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import flet as ft


def generate_l_size_image(
        qr_url, text_line1, text_line2, bottom_text_upper, lyricist, composer, arranger,
        notes_text, source_img_path=None
):
    """
    入力値から高解像度のL判画像を生成し、Bytesデータで返す関数
    """
    width = 1500
    height = 1051
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 1. 中央の縦の黒線
    center_x = width // 2
    draw.line((center_x, 0, center_x, height), fill=(0, 0, 0), width=5)

    # 2. 左側：正方形写真の加工・配置
    photo_bottom_y = 552  # 写真がない場合の初期値
    if source_img_path and os.path.exists(source_img_path):
        try:
            kujira = Image.open(source_img_path)
            square_size = 550
            gap = (center_x - square_size) // 2

            # 正方形にトリミング
            kujira = ImageOps.fit(kujira, (square_size, square_size), Image.Resampling.LANCZOS)

            paste_x = gap
            paste_y = gap
            if kujira.mode == 'RGBA':
                image.paste(kujira, (paste_x, paste_y), mask=kujira)
            else:
                image.paste(kujira, (paste_x, paste_y))

            # 写真の枠線
            border_offset = 2
            draw.rectangle(
                [paste_x - border_offset, paste_y - border_offset,
                 paste_x + kujira.width + border_offset, paste_y + kujira.height + border_offset],
                outline=(0, 0, 0), width=3
            )
            photo_bottom_y = paste_y + kujira.height + border_offset
        except Exception:
            pass

    # 3. フォントの設定
    font_path = "msgothic.ttc"
    if os.name != 'nt':
        font_path = "/System/Library/Fonts/FontsAvailableAtRuntime/HiraginoSans-W3.ttc"
        if not os.path.exists(font_path):
            font_path = "Arial.ttf"

    try:
        font1 = ImageFont.truetype(font_path, 40)
        font2 = ImageFont.truetype(font_path, 30)
        font_notes = ImageFont.truetype(font_path, 35)
        font_bottom_right1 = ImageFont.truetype(font_path, 52)
        font_bottom_right2 = ImageFont.truetype(font_path, 35)
        font_inside_box = ImageFont.truetype(font_path, 28)
    except IOError:
        font1 = font2 = font_notes = font_bottom_right1 = font_bottom_right2 = font_inside_box = ImageFont.load_default()

    # 4. サイズ取得（安全なメソッドを使用）
    h1 = font1.getbbox(text_line1)[3] - font1.getbbox(text_line1)[1] if text_line1 else 40
    h2 = font2.getbbox(text_line2)[3] - font2.getbbox(text_line2)[1] if text_line2 else 30
    single_h = font_bottom_right2.getbbox("作")[3] - font_bottom_right2.getbbox("作")[1]

    line_spacing = 15

    # 日付位置の基準
    block_start_y = photo_bottom_y + ((height - 20 - 25 - 70) - photo_bottom_y) // 2 - ((h1 + line_spacing + 30) // 2)
    credit_start_y = block_start_y + h1 + line_spacing + 10

    # 再生バーの位置を作詞の1行目とぴったり一致させる
    player_center_y = credit_start_y + (single_h // 2)

    # 5. 左側：文字の描画
    if text_line1:
        w1 = int(draw.textlength(text_line1, font=font1))
        draw.text((center_x // 2 - (w1 // 2), block_start_y), text_line1, fill=(0, 0, 0), font=font1)
    if text_line2:
        w2 = int(draw.textlength(text_line2, font=font2))
        draw.text((center_x // 2 - (w2 // 2), block_start_y + h1 + line_spacing), text_line2, fill=(0, 0, 0),
                  font=font2)

    # 6. 左側：音楽再生マークの描画
    bar_w = 450
    bar_x1 = center_x // 2 - (bar_w // 2)
    bar_x2 = center_x // 2 + (bar_w // 2)
    draw.line((bar_x1, player_center_y, bar_x2, player_center_y), fill=(200, 200, 200), width=4)
    current_x = bar_x1 + (bar_w // 3)
    draw.line((bar_x1, player_center_y, current_x, player_center_y), fill=(0, 0, 0), width=4)
    draw.ellipse((current_x - 6, player_center_y - 6, current_x + 6, player_center_y + 6), fill=(0, 0, 0))

    play_size = 25
    buttons_y = player_center_y + 70
    draw.polygon([(center_x // 2 - (play_size // 2), buttons_y - play_size),
                  (center_x // 2 - (play_size // 2), buttons_y + play_size),
                  (center_x // 2 + play_size, buttons_y)], fill=(0, 0, 0))

    skip_r_x = center_x // 2 + 120
    draw.polygon([(skip_r_x, buttons_y - 15), (skip_r_x, buttons_y + 15), (skip_r_x + 20, buttons_y)], fill=(0, 0, 0))
    draw.line((skip_r_x + 23, buttons_y - 15, skip_r_x + 23, buttons_y + 15), fill=(0, 0, 0), width=4)

    skip_l_x = center_x // 2 - 120
    draw.polygon([(skip_l_x, buttons_y - 15), (skip_l_x, buttons_y + 15), (skip_l_x - 20, buttons_y)], fill=(0, 0, 0))
    draw.line((skip_l_x - 23, buttons_y - 15, skip_l_x - 23, buttons_y + 15), fill=(0, 0, 0), width=4)

    # 7. 右側：「備考」の文字と「内容の枠線」の描画
    gap_value = (center_x - 550) // 2
    draw.text((center_x + gap_value, gap_value - 40), "備考", fill=(0, 0, 0), font=font_notes)
    box_x1 = center_x + gap_value
    box_y1 = gap_value + 15
    box_x2 = width - gap_value
    box_y2 = photo_bottom_y
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=(0, 0, 0), width=3)

    # 8. 右側：備考テキスト（改行対応）
    inside_text_y = box_y1 + 25
    if notes_text:
        for line in notes_text.splitlines():
            draw.text((box_x1 + 25, inside_text_y), line, fill=(50, 50, 50), font=font_inside_box)
            inside_text_y += 45

            # 9. 右側：URLから本物のQRコードを作成
    qr_size = 120
    qr_x = box_x2 - qr_size - 15
    qr_y = box_y2 - qr_size - 15
    if qr_url:
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=1, border=0)
            qr.add_data(qr_url)
            qr.make(fit=True)
            real_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            real_qr = real_qr.resize((qr_size, qr_size), Image.Resampling.NEAREST)

            try:
                parsed_url = urllib.parse.urlparse(qr_url)
                domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path.split('/')
                favicon_api = f"https://google.com{domain}&sz=64"
                req = urllib.request.Request(favicon_api, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=2) as response:
                    icon_data = response.read()
                logo = Image.open(io.BytesIO(icon_data)).convert("RGBA")
                logo_max_size = qr_size // 4
                logo = logo.resize((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
                real_qr.paste(logo, ((qr_size - logo.width) // 2, (qr_size - logo.height) // 2), mask=logo)
            except Exception:
                pass

            image.paste(real_qr, (qr_x, qr_y))
        except Exception:
            pass

    # 10. 右側：最下部エリアの文字配置
    right_area_center_x = center_x + (width - center_x) // 2
    if bottom_text_upper:
        w_upper = int(draw.textlength(bottom_text_upper, font=font_bottom_right1))
        draw.text((right_area_center_x - (w_upper // 2), block_start_y), bottom_text_upper, fill=(0, 0, 0),
                  font=font_bottom_right1)

    credits = [f"作詞：{lyricist}", f"作曲：{composer}", f"編曲：{arranger}"]
    max_credit_w = 0
    for line in credits:
        current_w = int(draw.textlength(line, font=font_bottom_right2))
        max_credit_w = max(max_credit_w, current_w)

    aligned_credit_x = right_area_center_x - (max_credit_w // 2)
    current_credit_y = credit_start_y
    for line in credits:
        draw.text((aligned_credit_x, current_credit_y), line, fill=(0, 0, 0), font=font_bottom_right2)
        current_credit_y += 45

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    return img_byte_arr.getvalue()


import base64


def main(page: ft.Page):
    page.title = "L判写真ジェネレーター"
    page.window_width = 800
    page.window_height = 950
    page.theme_mode = ft.ThemeMode.LIGHT

    selected_image_path = ft.Text("画像が選択されていません (デフォルト白地)", italic=True, size=12)

    # フォームの各テキスト入力フィールド
    tf_url = ft.TextField(label="QRコードのURL")
    tf_line1 = ft.TextField(label="曲名")
    tf_line2 = ft.TextField(label="アーティスト名")
    tf_date = ft.TextField(label="リリース年月日")
    tf_lyricist = ft.TextField(label="作詞")
    tf_composer = ft.TextField(label="作曲")
    tf_arranger = ft.TextField(label="編曲")

    # 備考欄用（1つに統合、複数行・改行対応）
    tf_notes = ft.TextField(label="備考内容", multiline=True, min_lines=3, max_lines=6)

    # プレビュー表示用のImageコンポーネント
    preview_img = ft.Image(width=600, height=420, fit=ft.ImageFit.CONTAIN)

    def update_preview(e=None):
        """入力値を読み取って画像を生成し、プレビューを更新する関数"""
        img_bytes = generate_l_size_image(
            qr_url=tf_url.value,
            text_line1=tf_line1.value,
            text_line2=tf_line2.value,
            bottom_text_upper=tf_date.value,
            lyricist=tf_lyricist.value,
            composer=tf_composer.value,
            arranger=tf_arranger.value,
            notes_text=tf_notes.value,
            source_img_path=selected_image_path.value if os.path.exists(str(selected_image_path.value)) else None
        )
        preview_img.src_base64 = base64.b64encode(img_bytes).decode("utf-8")
        page.update()

    # ファイルピッカー（画像選択用）
    def pick_files_result(e: ft.FilePickerResultEvent):
        # ★ [完全修正] e.filesの1番目の要素を指定して .path を正しく取得します
        if e.files and len(e.files) > 0:
            selected_image_path.value = e.files[0].path
            selected_image_path.italic = False
            update_preview()
        page.update()

    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)

    # すべての入力フィールドの変更イベントを紐付け
    all_fields = [
        tf_url, tf_line1, tf_line2, tf_date, tf_lyricist, tf_composer, tf_arranger, tf_notes
    ]
    for tf in all_fields:
        tf.on_change = update_preview

    # JPEG書き出し＆保存
    def save_image_file(e):
        img_bytes = generate_l_size_image(
            qr_url=tf_url.value,
            text_line1=tf_line1.value,
            text_line2=tf_line2.value,
            bottom_text_upper=tf_date.value,
            lyricist=tf_lyricist.value,
            composer=tf_composer.value,
            arranger=tf_arranger.value,
            notes_text=tf_notes.value,
            source_img_path=selected_image_path.value if os.path.exists(str(selected_image_path.value)) else None
        )
        with open("white.jpg", "wb") as f:
            f.write(img_bytes)
        page.open(ft.SnackBar(ft.Text("white.jpg として高画質画像を保存しました！")))

    # アプリ起動時に初期プレビューを描画
    update_preview()

    # 全体の要素を縦に並べるための最外枠 Column
    main_layout = ft.Column(
        [
            ft.Text("楽曲・写真設定", size=18, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton(
                "左上の写真を選択...",
                icon=ft.Icons.IMAGE,
                on_click=lambda _: file_picker.pick_files(allow_multiple=False,
                                                          allowed_extensions=["png", "jpg", "jpeg"])
            ),
            selected_image_path,
            tf_url,
            tf_line1,
            tf_line2,
            tf_date,
            ft.Row([tf_lyricist, tf_composer, tf_arranger]),

            ft.Divider(height=20),
            ft.Text("備考欄設定", size=18, weight=ft.FontWeight.BOLD),
            tf_notes,

            ft.Divider(height=20),
            # プレビュー表示エリア
            ft.Text("完成プレビュー（L判比率）", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=preview_img,
                border=ft.border.all(1, "black26"),
                border_radius=4,
                padding=10,
                bgcolor="grey50",
                alignment=ft.alignment.center
            ),
            ft.Text("※文字入力を検知して自動でプレビューが更新されます。", size=12, color="black54"),
            ft.Divider(height=20),

            # 書き出しボタン
            ft.ElevatedButton(
                "高画質JPEGを書き出す",
                icon=ft.Icons.SAVE,
                on_click=save_image_file,
                style=ft.ButtonStyle(bgcolor="blue", color="white")
            ),
        ],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True
    )

    page.add(
        ft.Container(
            content=main_layout,
            padding=20,
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
