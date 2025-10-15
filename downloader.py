import os
import sys
import yt_dlp
import logging
from urllib.request import urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ベースとなるダウンロードフォルダ
BASE_DOWNLOAD_DIR = "nerdcore technos"

class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and (
                    value.endswith('.mp3') or
                    value.endswith('.wav') or
                    value.endswith('.m4a')
                ):
                    full_url = urljoin(self.base_url, value)
                    self.links.append(full_url)

class MusicDownloader:
    # ▼▼▼ 変更点 ▼▼▼
    # 初期化時にサブフォルダのパスを受け取るように変更
    def __init__(self, subfolder_path):
        # 指定されたサブフォルダを含めた完全なパスを作成
        full_download_path = os.path.join(BASE_DOWNLOAD_DIR, subfolder_path)
        os.makedirs(full_download_path, exist_ok=True)
        logger.info(f"📁 ダウンロード先フォルダ: {full_download_path}")

        self.ydl_opts = {
            'format': 'bestaudio/best',
            # ダウンロード先のパスを更新
            'outtmpl': f'{full_download_path}/%(title)s.%(ext)s',
            # ポストプロセッサをflacからmp3に変更
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # 高音質な320kbpsに設定
            }],
            # ▲▲▲ 変更点 ▲▲▲
            'extract_flat': False,
            'noplaylist': False,
            'ignoreerrors': False,
            'quiet': False,
            'verbose': True
        }

    def download(self, url, scrape_internal_links=False, source_type='auto_detect'):
        """指定されたURLからトラックをダウンロード"""
        try:
            logger.info(f"🎵 解析とダウンロードを開始: {url}")

            if source_type == 'auto_detect':
                source_type = self.detect_source_type(url)

            if source_type in ['soundcloud', 'bandcamp', 'direct_link']:
                if not any(platform in url for platform in ['soundcloud.com', 'bandcamp.com']):
                    logger.error("🚫 SoundCloudまたはBandcampのURLを指定してください。")
                    return False

            internal_links = []
            if scrape_internal_links or source_type == 'archive':
                internal_links = self.scrape_internal_links(url)

            self.download_track(url)

            for link in internal_links:
                self.download_track(link)

            return True

        except Exception as e:
            logger.error(f"⚠️ 予期せぬエラーが発生: {str(e)}")
            return False

    def detect_source_type(self, url):
        """URLからソースタイプを自動検出"""
        if 'archive.org' in url:
            return 'archive'
        elif 'soundcloud.com' in url:
            return 'soundcloud'
        elif 'bandcamp.com' in url:
            return 'bandcamp'
        else:
            return 'direct_link'

    def scrape_internal_links(self, url):
        """指定されたURLから内部リンクをスクレイピング"""
        logger.info(f"🔍 内部リンクをスクレイピング中: {url}")
        try:
            with urlopen(url) as response:
                html = response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"URLを開けませんでした: {e}")
            return []

        parser = LinkParser(url)
        parser.feed(html)
        logger.info(f"✨ 見つかった内部リンク: {parser.links}")
        return parser.links

    def download_track(self, url):
        """トラックをダウンロード"""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                logger.info(f"✅ トラック「{info.get('title', 'Unknown')}」のダウンロードが完了しました！")
            except Exception as e:
                logger.error(f"⚠️ ダウンロード中にエラーが発生: {str(e)}")

def main():
    # ▼▼▼ 変更点 ▼▼▼
    # 引数の数をチェック (URLxN + scrape_bool + source_type + subfolder)
    if len(sys.argv) < 5:
        logger.error("❌ 引数が不足しています。")
        print("使用方法: python downloader.py <URL1> ... <scrape_bool> <source_type> <subfolder>")
        sys.exit(1)

    # 最後の引数をサブフォルダとして取得
    subfolder = sys.argv[-1]
    source_type = sys.argv[-2]
    scrape_internal_links = sys.argv[-3].lower() == 'true'

    # URLを取得
    urls = sys.argv[1:-3]

    # MusicDownloaderにサブフォルダ名を渡す
    downloader = MusicDownloader(subfolder_path=subfolder)
    # ▲▲▲ 変更点 ▲▲▲

    for url in urls:
        success = downloader.download(url, scrape_internal_links, source_type)
        if not success:
            logger.error(f"❌ {url} のダウンロードに失敗しました。")

if __name__ == "__main__":
    main()
