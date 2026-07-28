import os
import json
import urllib.request
import xml.etree.ElementTree as ET
import re
import datetime
import ssl

DATABASE_FILE = "floyo_comfy_database.json"

# 無料・オープンソース系モデル（推奨）
FREE_OS_MODELS = [
    "LTX 2.3", "LTX-Video", "Wan 2.1", "Wan 2.2", "Wan-Video",
    "AnimateDiff", "HunyuanVideo", "Open-Sora", "CogVideoX", "SV3D", "SVD"
]

# 有料・Partner Node系モデル（注意喚起）
PAID_PARTNER_MODELS = [
    "Kling", "Seedance", "Moonvalley", "Pixverse", "Ideogram", "Nano Banana", "GPT Image 2"
]

def http_get_rss(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return resp.read()

def classify_cost_and_models(text):
    text_upper = text.upper()
    detected_free = [m for m in FREE_OS_MODELS if m.upper() in text_upper]
    detected_paid = [m for m in PAID_PARTNER_MODELS if m.upper() in text_upper]
    
    if "FLOYO" in text_upper and any(kw in text_upper for kw in ["PARTNER", "CREDIT", "WALLET", "FLOYO_"]):
        is_paid = True
    elif len(detected_paid) > 0 and len(detected_free) == 0:
        is_paid = True
    else:
        is_paid = False
        
    return {
        "is_free_os": not is_paid,
        "free_models": detected_free,
        "paid_models": detected_paid,
        "cost_badge": "Free / Open-Source" if not is_paid else "Paid / Partner Risk"
    }

def fetch_reddit_live_knowhow():
    """
    Crawls live Reddit RSS feeds for Floyo, ComfyUI, and AI Video generation.
    """
    print("Crawling live Reddit RSS feeds for Floyo & ComfyUI Video Workflows...", flush=True)
    reddit_entries = []
    
    rss_urls = [
        "https://www.reddit.com/r/comfyui/hot.rss",
        "https://www.reddit.com/r/comfyui/new.rss",
        "https://www.reddit.com/r/Floyo/hot.rss",
        "https://www.reddit.com/r/StableDiffusion/hot.rss",
        "https://www.reddit.com/r/AIAnime/hot.rss"
    ]
    
    seen_links = set()
    keywords = [
        "video", "i2v", "t2v", "ltx", "wan", "animatediff", "hunyuan", 
        "floyo", "workflow", "canvas", "consistency", "lipsync", "animation", "motion", "nodes"
    ]
    
    for url in rss_urls:
        try:
            xml_data = http_get_rss(url)
            root = ET.fromstring(xml_data)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for entry in entries:
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
                content_elem = entry.find('{http://www.w3.org/2005/Atom}content')
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.attrib.get('href', '') if link_elem is not None else ""
                updated = updated_elem.text if updated_elem is not None else datetime.datetime.now().strftime("%Y-%m-%d")
                content_raw = content_elem.text if content_elem is not None else ""
                
                if not link or link in seen_links:
                    continue
                    
                clean_content = re.sub(r'<[^>]+>', ' ', content_raw).strip()
                clean_content = re.sub(r'\s+', ' ', clean_content)
                
                full_text = (title + " " + clean_content).lower()
                is_relevant = any(kw in full_text for kw in keywords)
                
                if is_relevant:
                    seen_links.add(link)
                    date_str = updated.split('T')[0] if 'T' in updated else updated[:10]
                    
                    cost_info = classify_cost_and_models(title + " " + clean_content)
                    
                    category = "Reddit: リアルタイム話題"
                    if "floyo" in full_text or "canvas" in full_text:
                        category = "Floyo ワークフロー・新機能"
                    elif "wan" in full_text or "ltx" in full_text or "animatediff" in full_text:
                        category = "オープンソース動画モデル (Wan/LTX/AnimateDiff)"
                    elif "consistency" in full_text or "character" in full_text:
                        category = "キャラクター一貫性・作画維持"
                    elif "i2v" in full_text or "t2v" in full_text or "video" in full_text:
                        category = "ComfyUI 動画生成ノード・テクニック"
                        
                    summary = clean_content[:200] + "..." if len(clean_content) > 200 else clean_content
                    if not summary or ("submitted by" in summary and len(summary) < 60):
                        summary = f"Reddit コミュニティでの動画制作議論。ワークフローや最新ノードに関する投稿です。"
                        
                    sub_name = "/r/comfyui"
                    if "/r/Floyo" in url:
                        sub_name = "/r/Floyo"
                    elif "/r/StableDiffusion" in url:
                        sub_name = "/r/StableDiffusion"
                    elif "/r/AIAnime" in url:
                        sub_name = "/r/AIAnime"

                    reddit_entries.append({
                        "id": f"reddit-{len(reddit_entries)+1}",
                        "category": category,
                        "title": f"[{sub_name}] {title}",
                        "updated": date_str,
                        "source": f"Reddit {sub_name}",
                        "summary": summary,
                        "url": link,
                        "cost_badge": cost_info["cost_badge"],
                        "is_free_os": cost_info["is_free_os"],
                        "detected_free_models": cost_info["free_models"],
                        "detected_paid_models": cost_info["paid_models"],
                        "tags": ["Reddit", sub_name.replace("/r/", ""), cost_info["cost_badge"]] + cost_info["free_models"] + cost_info["paid_models"]
                    })
        except Exception as e:
            print(f"Failed to crawl RSS {url}: {e}", flush=True)

    print(f"Extracted {len(reddit_entries)} live Reddit video workflow entries.", flush=True)
    return reddit_entries

def get_curated_base_knowhow():
    """
    Returns base curated guide entries for Floyo & ComfyUI free-leaning video workflows.
    """
    return [
        {
            "id": "base-1",
            "category": "Floyo 推奨動画ワークフロー",
            "title": "LTX 2.3 オープンソース Image-to-Video 黄金構成",
            "updated": "2026-07-28",
            "source": "Floyo Workflow Guide & ComfyUI Standards",
            "summary": "Floyoで最も安定して低コスト/無料で動くLTX 2.3モデルを用いたImage-to-Video構成。入力画像の色調・輪郭を保ちつつスムーズなカメラワークとキャラモーションを実現。",
            "url": "https://github.com/",
            "cost_badge": "Free / Open-Source",
            "is_free_os": True,
            "detected_free_models": ["LTX 2.3", "LTX-Video"],
            "detected_paid_models": [],
            "tags": ["Floyo", "LTX 2.3", "Image-to-Video", "Free Model"],
            "details": {
                "recommended_nodes": ["Load Image", "LTXVideoSampler", "VAEDecode", "VHS_VideoCombine"],
                "fps": 24,
                "frame_count": 97,
                "key_tips": [
                    "プロンプトは動きの動詞 (e.g. camera pans right, hair floating in the wind) に特化させる",
                    "Floyo UIのCanvas JSONとしてロード可能で、Partner Nodeクレジットを消費しません"
                ]
            }
        },
        {
            "id": "base-2",
            "category": "オープンソース動画モデル",
            "title": "Wan 2.1 / Wan 2.2 高画質動画生成ノード構成 (ComfyUI / Floyo)",
            "updated": "2026-07-28",
            "source": "ComfyUI Community & Wan-Video Open Model Spec",
            "summary": "商用・個人利用ともに高品質なオープンソースモデル Wan 2.1 / 2.2 を用いたT2V/I2Vパイプライン。実写・アニメ両対応で破綻の少ない動画を生成。",
            "url": "https://github.com/",
            "cost_badge": "Free / Open-Source",
            "is_free_os": True,
            "detected_free_models": ["Wan 2.1", "Wan 2.2"],
            "detected_paid_models": [],
            "tags": ["ComfyUI", "Floyo", "Wan 2.1", "Wan 2.2", "Text-to-Video"],
            "details": {
                "recommended_nodes": ["WanVideoTextEncode", "WanVideoSampler", "HighResolutionVAEDecode"],
                "fps": 16,
                "frame_count": 81,
                "key_tips": [
                    "Wan 2.1 14B / 1.3B モデルの使い分けによりグラフィックメモリ負荷を最適化",
                    "AnimateDiffと組み合わせたハイブリッドアニメモーション生成が可能"
                ]
            }
        },
        {
            "id": "base-3",
            "category": "キャラクター一貫性・作画維持",
            "title": "Anime Next Scene & Qwen キャラクター一貫性カット動画",
            "updated": "2026-07-28",
            "source": "Anime Consistency Workflows & Floyo Subgraphs",
            "summary": "マルチカット動画制作において、1話・複数カットを通じたキャラの顔・衣装・髪型の一貫性を維持するノード設計。IP-Adapter & Reference Control併用。",
            "url": "https://github.com/",
            "cost_badge": "Free / Open-Source",
            "is_free_os": True,
            "detected_free_models": ["NetaYume Lumina", "Anima", "Z-Anime"],
            "detected_paid_models": [],
            "tags": ["Character Consistency", "Anime", "IP-Adapter", "Floyo Subgraph"],
            "details": {
                "recommended_nodes": ["Character Profile Subgraph", "IPAdapterApply", "Per-Cut I2V Block"],
                "fps": 24,
                "frame_count": 48,
                "key_tips": [
                    "最初に静止画でキャラシートを生成し、その画像ブロックを各カットのI2Vブロックに入力",
                    "フリーの軽量アニメモデル (NetaYume, Anima) をベースモデルとして統一"
                ]
            }
        },
        {
            "id": "base-4",
            "category": "注意喚起・有料Partnerモデル",
            "title": "Floyoにおける Partner Nodes (Kling / Seedance / Moonvalley) の扱いと判定",
            "updated": "2026-07-28",
            "source": "Floyo Safety & Cost Audit Guide",
            "summary": "Kling, Seedance, Moonvalley, Pixverse などのAPI連携ノード（末尾 `_floyo` または Partner Node 標記）はFloyoのAPIウォレット/クレジットを消費します。無制限の無料運用を行う場合はオープンソースモデルへの置換を推奨。",
            "url": "https://github.com/",
            "cost_badge": "Paid / Partner Risk",
            "is_free_os": False,
            "detected_free_models": [],
            "detected_paid_models": ["Kling", "Seedance", "Moonvalley", "Pixverse"],
            "tags": ["Partner Nodes", "Cost Audit", "API Wallet"],
            "details": {
                "recommended_nodes": ["Replace with LTX 2.3 or Wan 2.1"],
                "fps": 30,
                "frame_count": 120,
                "key_tips": [
                    "ワークフロー内の `class_type` が `_floyo` で終わるかチェック",
                    "無料運用を目指す場合は LTX 2.3 や Wan 2.1 への置き換えを実施"
                ]
            }
        }
    ]

def generate_database():
    print("Generating Floyo & ComfyUI Video Knowledge Database...", flush=True)
    curated = get_curated_base_knowhow()
    live_reddit = fetch_reddit_live_knowhow()
    
    total_data = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(curated) + len(live_reddit),
        "curated_knowhow": curated,
        "reddit_live_topics": live_reddit
    }
    
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {total_data['total_count']} items to {DATABASE_FILE}.", flush=True)

if __name__ == "__main__":
    generate_database()
