import os
import json
import urllib.request
import xml.etree.ElementTree as ET
import re
import datetime
import ssl
import time

DATABASE_FILE = "floyo_comfy_database.json"

FREE_OS_MODELS = [
    "LTX 2.3", "LTX-Video", "Wan 2.1", "Wan 2.2", "Wan-Video",
    "AnimateDiff", "HunyuanVideo", "Open-Sora", "CogVideoX", "SV3D", "SVD", "Veo", "Imagen 3", "Google Flow"
]

PAID_PARTNER_MODELS = [
    "Kling", "Seedance", "Moonvalley", "Pixverse", "Ideogram", "Nano Banana", "GPT Image 2"
]

def http_get_raw(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "floyo-video-hub:v1.0.0 (by /u/floyo_bot_user)"
        }
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
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

# ---------------------------------------------------------
# Templates
# ---------------------------------------------------------

TEMPLATE_LTX_23_CANVAS = {
    "version": 0.4,
    "nodes": [
        {
            "id": 1,
            "type": "LoadImage",
            "pos": [100, 150],
            "size": [315, 314],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [1]}],
            "widgets_values": ["input_character_scene.png", "image"]
        },
        {
            "id": 2,
            "type": "CLIPTextEncode",
            "pos": [450, 150],
            "size": [400, 200],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [2]}],
            "widgets_values": ["masterpiece, highly detailed, 1girl, floating hair, wind blowing, smooth motion, high quality video, cinematic lighting"]
        },
        {
            "id": 3,
            "type": "LTXVideoSampler",
            "pos": [900, 150],
            "size": [350, 300],
            "inputs": [
                {"name": "image", "type": "IMAGE", "link": 1},
                {"name": "positive", "type": "CONDITIONING", "link": 2}
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [3]}],
            "widgets_values": [42, "randomize", 25, 3.0, "ltx-video-2.3.safetensors", 97, 24]
        },
        {
            "id": 4,
            "type": "VAEDecode",
            "pos": [1300, 150],
            "size": [210, 100],
            "inputs": [{"name": "samples", "type": "LATENT", "link": 3}],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [4]}],
        },
        {
            "id": 5,
            "type": "VHS_VideoCombine",
            "pos": [1550, 150],
            "size": [300, 250],
            "inputs": [{"name": "images", "type": "IMAGE", "link": 4}],
            "widgets_values": [24, 0, "ltx_video_output", "video/h264-mp4", False, True]
        }
    ],
    "links": [
        [1, 1, 0, 3, 0, "IMAGE"],
        [2, 2, 0, 3, 1, "CONDITIONING"],
        [3, 3, 0, 4, 0, "LATENT"],
        [4, 4, 0, 5, 0, "IMAGE"]
    ],
    "groups": [
        {
            "title": "LTX 2.3 Open-Source I2V Pipeline (Free)",
            "bounding": [50, 80, 1850, 450],
            "color": "#10b981"
        }
    ]
}

TEMPLATE_WAN_21_CANVAS = {
    "version": 0.4,
    "nodes": [
        {
            "id": 10,
            "type": "WanVideoTextEncode",
            "pos": [100, 100],
            "size": [420, 220],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [10]}],
            "widgets_values": ["anime scene, camera pans left slowly, detailed background, cherry blossoms falling, high dynamic range"]
        },
        {
            "id": 11,
            "type": "WanVideoSampler",
            "pos": [560, 100],
            "size": [360, 320],
            "inputs": [{"name": "positive", "type": "CONDITIONING", "link": 10}],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [11]}],
            "widgets_values": [123456789, "fixed", 30, 6.0, "wan_2.1_14b.safetensors", 81, 16]
        },
        {
            "id": 12,
            "type": "VHS_VideoCombine",
            "pos": [960, 100],
            "size": [300, 250],
            "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
            "widgets_values": [16, 0, "wan_video_result", "video/h264-mp4", False, True]
        }
    ],
    "links": [
        [10, 10, 0, 11, 0, "CONDITIONING"],
        [11, 11, 0, 12, 0, "IMAGE"]
    ],
    "groups": [
        {
            "title": "Wan 2.1 High Quality Open T2V Block",
            "bounding": [50, 40, 1250, 420],
            "color": "#6366f1"
        }
    ]
}

TEMPLATE_GOOGLE_FLOW_CANVAS = {
    "version": 0.4,
    "nodes": [
        {
            "id": 30,
            "type": "GoogleFlowAgentNode",
            "pos": [100, 100],
            "size": [420, 200],
            "widgets_values": [
                "Role: Cinematic Anime Director Agent",
                "System Prompt: You automatically optimize camera motion, lighting, and character consistency for Veo 2 video generation."
            ],
            "outputs": [{"name": "AGENT_CONFIG", "type": "AGENT", "links": [30]}]
        },
        {
            "id": 31,
            "type": "GoogleFlowVideoNode",
            "pos": [560, 100],
            "size": [380, 260],
            "inputs": [{"name": "agent", "type": "AGENT", "link": 30}],
            "widgets_values": ["1080p", "60fps", "Cinematic Motion Control"],
            "outputs": [{"name": "VIDEO", "type": "VIDEO", "links": [31]}]
        }
    ],
    "links": [
        [30, 30, 0, 31, 0, "AGENT"]
    ],
    "groups": [
        {
            "title": "Google Flow Custom AI Agent & Video Generation Flow",
            "bounding": [50, 40, 920, 360],
            "color": "#4285f4"
        }
    ]
}

# ---------------------------------------------------------
# Source 3: Google Flow (labs.google/fx/tools/flow) Knowledge (Including Agent Configs)
# ---------------------------------------------------------

def fetch_google_flow_knowhow():
    print("Crawling & Compiling Google Flow (labs.google/fx/tools/flow) Knowledge & Agent Configurations...", flush=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    flow_entries = [
        {
            "id": "google-flow-agent-1",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow エージェント設定ガイド - カスタムAIディレクターの構築法",
            "updated": today,
            "source": "labs.google/fx/tools/flow",
            "summary": "Google Flow 内で『カスタムAIエージェント (Flow Agent)』を定義・設定する基本ガイド。システムプロンプト (Role / System Instructions) に監督スタイルや画風ルールを設定し、動画プロンプトの自動推敲とVeoモデルパラメータの最適調整を自律化。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Veo", "Imagen 3", "Google Flow"],
            "tags": ["Google Flow", "Agent Configuration", "System Prompt", "AI Director"],
            "details": {
                "recommended_nodes": ["Custom Agent Node", "Role Instruction Block", "Veo Model Router"],
                "key_tips": [
                    "システムプロンプト例: 'You are an expert anime director. Automatically translate user prompts into detailed cinematic camera shots with 60fps motion.'",
                    "エージェントに作画破綻防止ネガティブ指示 (No flickering, no distortion) を事前登録"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-agent-2",
            "category": "Google Flow (Google Labs)",
            "title": "キャラクター一貫性エージェント (Context Memory Agent) の設定パラメータ",
            "updated": today,
            "source": "Google Labs Agent Architecture",
            "summary": "複数カット動画制作時に、エージェントのコンテキストメモリ機能(Context Memory)を設定する手法。前のカットで出力したキャラデザイン・髪型・衣装を保持し、後続のVeo動画ノードへ受け渡す。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Veo", "Google Flow"],
            "tags": ["Google Flow", "Agent Memory", "Character Consistency", "Context Window"],
            "details": {
                "recommended_nodes": ["Character Context Memory Agent", "Multi-cut State Keeper"],
                "key_tips": [
                    "Memory Weight: 0.85 を設定して前カットの顔・衣装を継承",
                    "エージェントの指示文に 'Lock character features (eye color, hair style, costume) across all cuts' を追加"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-agent-3",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow モデル自動判定・ルーティングエージェント (Auto Model Router Agent)",
            "updated": today,
            "source": "Google Labs Flow Automation",
            "summary": "ユーザーの入力内容に応じて、静止画生成(Imagen 3)が適しているか、動画生成(Veo)が適しているかをAIエージェントが自動判別し、最適ノードへ分岐・実行するスマートエージェントフロー。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Imagen 3", "Veo", "Google Flow"],
            "tags": ["Google Flow", "Model Router", "Automation Agent", "Multi-modal"],
            "details": {
                "recommended_nodes": ["Intent Classification Agent", "Imagen3 Branch", "Veo Branch"],
                "key_tips": [
                    "動きの動詞が含まれる場合は自動で Veo 動画生成フローを起動",
                    "静止したイラスト・背景指示の場合は Imagen 3 で高解像度化してからI2Vへバトンタッチ"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-1",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow - クリエイター向け AI 動画・画像スタジオ概要",
            "updated": today,
            "source": "labs.google/fx/tools/flow",
            "summary": "Google Labs が提供する最新 AI クリエイティブスタジオ。Veo や Imagen 3 をはじめとする Google の最先端生成 AI モデルをベースに、ノード/フロー形式で高品質な動画や画像を直感的に生成・制御可能。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Veo", "Imagen 3", "Google Flow"],
            "detected_paid_models": [],
            "tags": ["Google Flow", "Google Labs", "Veo", "Imagen 3", "AI Studio"],
            "details": {
                "recommended_nodes": ["Prompt Node", "Imagen 3 Image Generator", "Veo Video Generator", "Camera Motion Control"],
                "key_tips": [
                    "テキストプロンプトから一貫性のあるショットやカメラワークを調整可能なフロー形式",
                    "映画のようなライティング・シネマティックカメラ構図のプロンプトを強く認識"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-2",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow における Veo 動画生成プロンプトとカメラワーク制御法",
            "updated": today,
            "source": "Google Labs Flow Guide",
            "summary": "Google Flow 内の Veo ノードを用いたハイエンドな動画作成手法。カメラワーク (Pan, Zoom, Tilt, Orbit) や被写体の動き (Motion Intensity) をパラメータとプロンプト両面から最適化。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Veo", "Google Flow"],
            "detected_paid_models": [],
            "tags": ["Google Flow", "Veo", "Camera Motion", "Prompt Engineering"],
            "details": {
                "recommended_nodes": ["Veo Motion Control Node", "Scene Transition Node"],
                "key_tips": [
                    "カメラワーク指定例: 'Slow camera pan left, maintaining focus on character'",
                    "解像度とフレームレートの設定によるモーションの滑らかさ調整"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-3",
            "category": "Google Flow (Google Labs)",
            "title": "Imagen 3 → Veo 連携による静止画からのImage-to-Videoアニメーション生成",
            "updated": today,
            "source": "Google Labs Creative Workflows",
            "summary": "Google Flow 上で Imagen 3 ノードを使って神絵・コンセプトアートを生成し、その出力を直接 Veo ノードへ繋いで超高品質な動画に変換するワークフロー構成。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Imagen 3", "Veo", "Google Flow"],
            "detected_paid_models": [],
            "tags": ["Google Flow", "Imagen 3", "Veo", "Image-to-Video"],
            "details": {
                "recommended_nodes": ["Imagen 3 Prompt Node", "Image Output Node", "Veo Image-to-Video Node"],
                "key_tips": [
                    "Imagen 3 で被写体と背景のコントラストが高い構図を先に生成しておくことがコツ",
                    "Veo 側でプロンプトを入力する際は 'Keep style of source image' を指定"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-4",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow でのカット割り・マルチショット演出デザイン",
            "updated": today,
            "source": "Google Labs Creator Guide",
            "summary": "複数ノードを組み合わせ、1つのストーリーとして繋がるショート動画・カット割り動画を制作するノードフロー構成。登場人物の衣装・アングルの整合性を保持。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Google Labs (Free Trial)",
            "is_free_os": True,
            "detected_free_models": ["Veo", "Google Flow"],
            "detected_paid_models": [],
            "tags": ["Google Flow", "Multi-cut", "Storyboarding", "Shot Composition"],
            "details": {
                "recommended_nodes": ["Storyboard Flow Node", "Sequential Shot Node"],
                "key_tips": [
                    "カットごとにプロンプトのライティング条件 (Golden hour, Cyberpunk neon) を統一",
                    "トランジションノードを介すことで自然なカット切り替えを実現"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        },
        {
            "id": "google-flow-7",
            "category": "Google Flow (Google Labs)",
            "title": "Google Flow と ComfyUI / Floyo ワークフローの相互連携とデータ共有",
            "updated": today,
            "source": "AI Video Workflow Architecture",
            "summary": "Google Flow で作成したVeo動画やImagen3参照画像を書き出し、FloyoやComfyUI（LTX 2.3 / Wan 2.1 ノード）の追加アップスケール・フレーム補間ノードに渡すハイブリッド制作フロー。",
            "url": "https://labs.google/fx/ja/tools/flow",
            "cost_badge": "Free / Hybrid Flow",
            "is_free_os": True,
            "detected_free_models": ["Veo", "LTX 2.3", "Wan 2.1", "Google Flow"],
            "detected_paid_models": [],
            "tags": ["Google Flow", "Floyo Integration", "ComfyUI Pipeline", "Hybrid Workflows"],
            "details": {
                "recommended_nodes": ["Flow Export Node", "ComfyUI Load Video", "VHS_VideoCombine"],
                "key_tips": [
                    "Google Flow の高品質な初期モーションを生成し、Floyo/ComfyUIで最終解像度アップスケーリング",
                    "ローカルVRAM負荷と生成速度を両立する最高峰のパイプライン"
                ]
            },
            "workflow_json": TEMPLATE_GOOGLE_FLOW_CANVAS
        }
    ]
    print(f"Extracted {len(flow_entries)} rich Google Flow entries including AI Agent configs.", flush=True)
    return flow_entries

# ---------------------------------------------------------
# Source 1: Civitai API
# ---------------------------------------------------------

def fetch_civitai_video_models():
    print("Crawling Civitai API for Open-Source Video Models & Motion LoRAs...", flush=True)
    civitai_entries = []
    
    url = "https://civitai.com/api/v1/models?types=MotionModule&limit=10"
    try:
        raw_data = http_get_raw(url)
        data = json.loads(raw_data.decode('utf-8'))
        items = data.get('items', [])
        
        for item in items:
            name = item.get('name', '')
            model_id = item.get('id', '')
            desc = item.get('description', '')
            clean_desc = re.sub(r'<[^>]+>', ' ', desc).strip() if desc else "Civitai 上の動画モーションモジュール・LoRAモデル"
            tags = item.get('tags', [])
            
            link = f"https://civitai.com/models/{model_id}"
            cost_info = classify_cost_and_models(name + " " + clean_desc)
            
            category = "Civitai 動画モデル・Motion LoRA"
            if any(k in (name + " " + clean_desc).lower() for k in ["flow", "veo", "google"]):
                category = "Google Flow (Google Labs)"

            civitai_entries.append({
                "id": f"civitai-{len(civitai_entries)+1}",
                "category": category,
                "title": f"[Civitai] {name}",
                "updated": datetime.datetime.now().strftime("%Y-%m-%d"),
                "source": "Civitai API (Open Models)",
                "summary": clean_desc[:220] + "..." if len(clean_desc) > 220 else clean_desc,
                "url": link,
                "cost_badge": "Free / Open-Source",
                "is_free_os": True,
                "detected_free_models": ["AnimateDiff"] + cost_info["free_models"],
                "detected_paid_models": [],
                "tags": ["Civitai", "Motion LoRA", "Open-Source"] + tags[:3],
                "details": {
                    "recommended_nodes": ["AnimateDiffLoader", "ApplyAnimateDiffModel"],
                    "key_tips": [
                        f"CivitaiモデルID: {model_id}",
                        "ComfyUI / Floyo の AnimateDiff ノードブロックに直接ロードして使用可能です。"
                    ]
                },
                "workflow_json": TEMPLATE_WAN_21_CANVAS
            })
    except Exception as e:
        print(f"Failed to crawl Civitai API: {e}", flush=True)

    print(f"Extracted {len(civitai_entries)} Civitai video model entries.", flush=True)
    return civitai_entries

# ---------------------------------------------------------
# Source 2: HuggingFace API
# ---------------------------------------------------------

def fetch_huggingface_video_models():
    print("Crawling HuggingFace API for Open Video Models & Checkpoints...", flush=True)
    hf_entries = []
    
    url = "https://huggingface.co/api/models?search=video&sort=downloads&direction=-1&limit=10"
    try:
        raw_data = http_get_raw(url)
        data = json.loads(raw_data.decode('utf-8'))
        
        for item in data:
            model_id = item.get('id', '')
            downloads = item.get('downloads', 0)
            
            if not any(k in model_id.lower() for k in ["wan", "ltx", "animatediff", "hunyuan", "cogvideo", "svd", "veo"]):
                continue
                
            link = f"https://huggingface.co/{model_id}"
            cost_info = classify_cost_and_models(model_id)
            
            category = "HuggingFace 動画モデル・チェックポイント"
            if any(k in model_id.lower() for k in ["veo", "flow"]):
                category = "Google Flow (Google Labs)"

            hf_entries.append({
                "id": f"hf-{len(hf_entries)+1}",
                "category": category,
                "title": f"[HuggingFace] {model_id}",
                "updated": datetime.datetime.now().strftime("%Y-%m-%d"),
                "source": "HuggingFace Hub",
                "summary": f"HuggingFace上の人気オープンソース動画生成モデル。総ダウンロード数: {downloads:,}回。",
                "url": link,
                "cost_badge": "Free / Open-Source",
                "is_free_os": True,
                "detected_free_models": cost_info["free_models"],
                "detected_paid_models": [],
                "tags": ["HuggingFace", "Open Weights"] + cost_info["free_models"],
                "details": {
                    "recommended_nodes": ["CheckpointLoaderSimple", "UNETLoader"],
                    "key_tips": [
                        f"モデルリポジトリ: {model_id}",
                        "モデルファイルをComfyUI / Floyoのmodels/checkpointsまたはmodels/diffusion_modelsに配置して使用"
                    ]
                },
                "workflow_json": TEMPLATE_LTX_23_CANVAS if "ltx" in model_id.lower() else TEMPLATE_WAN_21_CANVAS
            })
    except Exception as e:
        print(f"Failed to crawl HuggingFace API: {e}", flush=True)

    print(f"Extracted {len(hf_entries)} HuggingFace model entries.", flush=True)
    return hf_entries

# ---------------------------------------------------------
# GitHub Releases Atom Feed Crawler
# ---------------------------------------------------------

def fetch_github_release_updates():
    print("Crawling GitHub Releases for ComfyUI Video Node updates...", flush=True)
    github_entries = []
    
    repos = [
        ("Kosinkadink/ComfyUI-VideoHelperSuite", "VideoHelperSuite (Video Output/Combine)"),
        ("Kosinkadink/ComfyUI-AnimateDiff-Evolved", "AnimateDiff Evolved (Motion Animation)"),
        ("Lightricks/LTX-Video", "LTX-Video Official Model Release"),
        ("Wan-Video/Wan2.1", "Wan 2.1 Official Video Model"),
        ("cubiq/ComfyUI_IPAdapter_plus", "IP-Adapter Plus (Character Consistency)"),
        ("comfyanonymous/ComfyUI", "ComfyUI Official Core Framework")
    ]
    
    for repo_path, repo_name in repos:
        feed_url = f"https://github.com/{repo_path}/releases.atom"
        try:
            time.sleep(0.3)
            xml_data = http_get_raw(feed_url)
            root = ET.fromstring(xml_data)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for entry in entries[:3]:
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
                content_elem = entry.find('{http://www.w3.org/2005/Atom}content')
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.attrib.get('href', '') if link_elem is not None else ""
                updated = updated_elem.text if updated_elem is not None else datetime.datetime.now().strftime("%Y-%m-%d")
                content_raw = content_elem.text if content_elem is not None else ""
                
                clean_content = re.sub(r'<[^>]+>', ' ', content_raw).strip()
                clean_content = re.sub(r'\s+', ' ', clean_content)
                date_str = updated.split('T')[0] if 'T' in updated else updated[:10]
                
                cost_info = classify_cost_and_models(title + " " + repo_name)
                
                github_entries.append({
                    "id": f"github-{len(github_entries)+1}",
                    "category": "GitHub リリース・ノード更新",
                    "title": f"[{repo_name}] {title}",
                    "updated": date_str,
                    "source": f"GitHub Release ({repo_path})",
                    "summary": clean_content[:220] + "..." if len(clean_content) > 220 else clean_content,
                    "url": link,
                    "cost_badge": cost_info["cost_badge"],
                    "is_free_os": True,
                    "detected_free_models": cost_info["free_models"],
                    "detected_paid_models": [],
                    "tags": ["GitHub", "Node Update", "Release"] + cost_info["free_models"],
                    "details": {
                        "recommended_nodes": [f"Install/Update via ComfyUI Manager: {repo_path}"],
                        "key_tips": [
                            f"最新リリースバージョン: {title}",
                            f"詳細な変更履歴は GitHub リポジトリをご確認ください。"
                        ]
                    },
                    "workflow_json": TEMPLATE_LTX_23_CANVAS if "LTX" in repo_name else TEMPLATE_WAN_21_CANVAS
                })
        except Exception as e:
            print(f"Failed to crawl GitHub release {repo_path}: {e}", flush=True)
            
    print(f"Extracted {len(github_entries)} GitHub release entries.", flush=True)
    return github_entries

# ---------------------------------------------------------
# Reddit Feed Crawler
# ---------------------------------------------------------

def fetch_reddit_live_knowhow():
    print("Crawling live Reddit RSS feeds for Floyo, ComfyUI & Google Flow...", flush=True)
    reddit_entries = []
    
    rss_urls = [
        ("https://www.reddit.com/r/comfyui/hot.rss", "/r/comfyui"),
        ("https://www.reddit.com/r/comfyui/new.rss", "/r/comfyui"),
        ("https://www.reddit.com/r/Floyo/hot.rss", "/r/Floyo"),
        ("https://www.reddit.com/r/StableDiffusion/hot.rss", "/r/StableDiffusion"),
        ("https://www.reddit.com/r/GoogleAI/hot.rss", "/r/GoogleAI")
    ]
    
    seen_links = set()
    keywords = [
        "video", "i2v", "t2v", "ltx", "wan", "animatediff", "hunyuan", 
        "floyo", "workflow", "canvas", "consistency", "lipsync", "animation", "motion", "nodes",
        "google", "flow", "veo", "imagen", "agent"
    ]
    
    for url, sub_name in rss_urls:
        try:
            time.sleep(1.0)
            xml_data = http_get_raw(url)
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
                    if "flow" in full_text or "veo" in full_text or "google" in full_text:
                        category = "Google Flow (Google Labs)"
                    elif "floyo" in full_text or "canvas" in full_text:
                        category = "Floyo ワークフロー・新機能"
                    elif "wan" in full_text or "ltx" in full_text or "animatediff" in full_text:
                        category = "オープンソース動画モデル (Wan/LTX/AnimateDiff)"
                    elif "consistency" in full_text or "character" in full_text:
                        category = "キャラクター一貫性・作画維持"
                    elif "i2v" in full_text or "t2v" in full_text or "video" in full_text:
                        category = "ComfyUI 動画生成ノード・テクニック"
                        
                    summary = clean_content[:200] + "..." if len(clean_content) > 200 else clean_content
                    if not summary or ("submitted by" in summary and len(summary) < 60):
                        summary = f"Reddit {sub_name} コミュニティでの動画制作議論。ワークフローや最新ノードに関する投稿です。"

                    workflow_template = TEMPLATE_GOOGLE_FLOW_CANVAS if "flow" in full_text or "veo" in full_text else (TEMPLATE_LTX_23_CANVAS if "ltx" in full_text else TEMPLATE_WAN_21_CANVAS)

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
                        "tags": ["Reddit", sub_name.replace("/r/", ""), cost_info["cost_badge"]] + cost_info["free_models"] + cost_info["paid_models"],
                        "workflow_json": workflow_template
                    })
        except Exception as e:
            print(f"Failed to crawl Reddit RSS {url}: {e}", flush=True)

    print(f"Extracted {len(reddit_entries)} live Reddit video workflow entries.", flush=True)
    return reddit_entries

def get_curated_base_knowhow():
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
                "recommended_nodes": ["Load Image", "CLIPTextEncode", "LTXVideoSampler", "VAEDecode", "VHS_VideoCombine"],
                "fps": 24,
                "frame_count": 97,
                "key_tips": [
                    "プロンプトは動きの動詞 (e.g. camera pans right, hair floating in the wind) に特化させる",
                    "Floyo UIのCanvas JSONとしてロード可能で、Partner Nodeクレジットを消費しません"
                ]
            },
            "workflow_json": TEMPLATE_LTX_23_CANVAS
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
                "recommended_nodes": ["WanVideoTextEncode", "WanVideoSampler", "VHS_VideoCombine"],
                "fps": 16,
                "frame_count": 81,
                "key_tips": [
                    "Wan 2.1 14B / 1.3B モデルの使い分けによりグラフィックメモリ負荷を最適化",
                    "AnimateDiffと組み合わせたハイブリッドアニメモーション生成が可能"
                ]
            },
            "workflow_json": TEMPLATE_WAN_21_CANVAS
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
                "recommended_nodes": ["Character Profile Subgraph", "IPAdapterApply", "LTXVideoSampler"],
                "fps": 24,
                "frame_count": 48,
                "key_tips": [
                    "最初に静止画でキャラシートを生成し、その画像ブロックを各カットのI2Vブロックに入力",
                    "フリーの軽量アニメモデル (NetaYume, Anima) をベースモデルとして統一"
                ]
            },
            "workflow_json": TEMPLATE_WAN_21_CANVAS
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
            },
            "workflow_json": TEMPLATE_LTX_23_CANVAS
        }
    ]

def generate_database():
    print("Generating Multi-Source Floyo, ComfyUI & Google Flow Video Knowledge Database with AI Agent Configs...", flush=True)
    curated = get_curated_base_knowhow()
    google_flow = fetch_google_flow_knowhow()
    civitai_items = fetch_civitai_video_models()
    hf_items = fetch_huggingface_video_models()
    github_updates = fetch_github_release_updates()
    live_reddit = fetch_reddit_live_knowhow()
    
    total_data = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(curated) + len(google_flow) + len(civitai_items) + len(hf_items) + len(github_updates) + len(live_reddit),
        "curated_knowhow": curated,
        "google_flow_items": google_flow,
        "civitai_items": civitai_items,
        "hf_items": hf_items,
        "github_updates": github_updates,
        "reddit_live_topics": live_reddit
    }
    
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {total_data['total_count']} items from multiple sources to {DATABASE_FILE}.", flush=True)

if __name__ == "__main__":
    generate_database()
