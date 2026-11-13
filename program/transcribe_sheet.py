"""
古琴琴谱拍照转录工具 (Guqin Sheet Vision Transcriber)
-----------------------------------------------------------
用法:
  python transcribe_sheet.py <图片路径> [--output 输出JSON路径]

示例:
  python transcribe_sheet.py IMG_0961.jpeg -o daoyi_page6.json
"""

import sys
import os
import json
import argparse

VISION_PROMPT_TEMPLATE = """
你是一位精通古琴记谱法与减字谱的音乐转录专家。
请仔细分析这张古琴乐谱图片，严格将其提取为结构化 JSON 格式。

识别要求：
1. 提取曲谱基本信息：title (曲名), key (调号，如 1=bB 或 1=F), tuning (定弦), tempo (速度，如 ♩=66)。
2. 将每个小节拆解为 measures 数组：
   - barNumber: 小节序号 (整数)
   - isPhraseStart: 是否为乐句开头 (布尔值)
   - sectionTitle: 段落标记 (如 "[一] ♩=72", 若无则为 null)
   - notes: 包含小节内所有音符对象的数组：
     - pitch: 简谱音级 (1~7 整数)
     - octave: 八度点 (-1 为低音点, 0 为中音, 1 为高音点)
     - accidental: 升降号 ("#" 或 "b"，无则为 null)
     - isHarmonic: 是否为泛音 (若音符上有小圆圈 ° 则为 true)
     - isGlide: 是否为走手音/滑音 (若有连音弧线终点则为 true)
     - finger: 对应的减字谱指法 (如 "名九", "勾五", "挑六", "散七", "大七", "外")
     - underline: 减时线下划线数量 (0 为四分音符无下划线, 1 为八分音符单线, 2 为十六分音符双线)
     - hasDot: 是否有附点 (布尔值)
     - dashes: 延音增时横线数量 (如 "3 - - -" 为 3, "5. -" 为 1)

请严格仅输出合法 JSON 文本，不要带有任何额外的自然语言解释。
"""

def generate_mock_transcription(image_path):
    """
    内置离线校对标准模板，用于在无云端 API 时快速验证导入导出闭环
    """
    base_name = os.path.basename(image_path)
    print(f"[*] 正在分析图片: {base_name}")
    print("[*] 正在提取减字谱指法与简谱音高流...")

    return {
        "title": "捣衣 (AI转录版)",
        "subtitle": "古曲 · 钱秀山演奏谱 · 许健记谱 (拍照提取)",
        "key": "1 = ♭B",
        "tuning": "紧五慢一定弦: 1: 3: 5: 6. 1. 2. 3.",
        "tempo": "♩ = 66",
        "pageNumber": "AI-1",
        "measures": [
            {
                "barNumber": 1,
                "isPhraseStart": True,
                "notes": [
                    { "id": "ai-1-1", "pitch": 3, "octave": 0, "finger": "名九", "underline": 1, "hasDot": True, "dashes": 0, "isGlide": False, "isHarmonic": False },
                    { "id": "ai-1-2", "pitch": 2, "octave": 0, "finger": "注十", "underline": 2, "hasDot": False, "dashes": 0, "isGlide": True,  "isHarmonic": False },
                    { "id": "ai-1-3", "pitch": 1, "octave": 0, "finger": "勾五", "underline": 0, "hasDot": False, "dashes": 0, "isGlide": False, "isHarmonic": False },
                    { "id": "ai-1-4", "pitch": 2, "octave": 0, "finger": "挑六", "underline": 0, "hasDot": False, "dashes": 0, "isGlide": False, "isHarmonic": False }
                ]
            },
            {
                "barNumber": 2,
                "isPhraseStart": False,
                "notes": [
                    { "id": "ai-2-1", "pitch": 3, "octave": 0, "finger": "勾五", "underline": 0, "hasDot": False, "dashes": 3, "isGlide": False, "isHarmonic": False }
                ]
            }
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="古琴琴谱拍照转录工具")
    parser.add_argument("image", help="琴谱图片路径 (如 IMG_0961.jpeg)")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[!] 错误: 找不到图片文件: {args.image}")
        sys.exit(1)

    out_file = args.output
    if not out_file:
        base, _ = os.path.splitext(args.image)
        out_file = f"{base}_score.json"

    # 若环境配置了 GEMINI_API_KEY，可直接调用云端大模型接口
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[!] 错误: 未检测到环境变量 GEMINI_API_KEY。")
        print("[i] 拍照识谱需要调用大模型 Vision 接口，请先设置环境变量：$env:GEMINI_API_KEY='your_key'")
        print("[i] 提示：当前系统已全量内置《捣衣》(20小节)与《春风》(26小节)，您可直接在网页下拉框中选择开练！")
        sys.exit(1)

    print("[*] 检测到 GEMINI_API_KEY，正在调用云端 Vision API 进行高精度转录...")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        from PIL import Image
        img = Image.open(args.image)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[img, VISION_PROMPT_TEMPLATE]
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(lines[1:-1])
        data = json.loads(raw_text)
    except Exception as e:
        print(f"[!] 云端 Vision API 转录失败: {e}")
        print("[i] 请检查图片路径、网络连接或 API Key 权限。")
        sys.exit(1)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[✓] 转录完成！曲谱数据已保存至: {out_file}")
    print(f"[i] 你可以在浏览器工作台中点击【⬆ 导入谱文件】载入此文件立即开练！")

if __name__ == "__main__":
    main()

