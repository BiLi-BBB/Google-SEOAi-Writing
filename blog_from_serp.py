import time
import os
import streamlit as st
from openai import OpenAI
import json
import re
#比利微信:8845665
# 设置页面配置（必须是第一个 Streamlit 命令）
st.set_page_config(
    page_title="AI Blog Writer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 文章大小定义
ARTICLE_SIZES = {
    '标准长度': {
        'description': '生成标准长度的段落，每段约300-400字',
        'tokens_per_section': 500
    },
    '较短长度': {
        'description': '生成较短的段落，每段约200-300字',
        'tokens_per_section': 300
    },
    '较长长度': {
        'description': '生成较长的段落，每段约500-600字',
        'tokens_per_section': 800
    }
}

# 文章风格选项
TONE_OF_VOICE = {
    'None': 'No specific tone, use natural writing style',
    'Friendly': 'Warm and approachable tone, building rapport with readers',
    'Professional': 'Business-like and competent tone, maintaining credibility',
    'Informational': 'Educational and explanatory tone, focusing on facts',
    'Transactional': 'Action-oriented tone, encouraging specific responses',
    'Inspirational': 'Uplifting and motivational tone, inspiring action',
    'Neutral': 'Balanced and unbiased tone, presenting facts objectively',
    'Witty': 'Clever and humorous tone, engaging through wordplay',
    'Casual': 'Relaxed and informal tone, like talking to a friend',
    'Authoritative': 'Expert and commanding tone, demonstrating expertise',
    'Encouraging': 'Supportive and positive tone, building confidence',
    'Persuasive': 'Convincing and influential tone, driving decisions',
    'Poetic': 'Artistic and expressive tone, using creative language'
}

POINT_OF_VIEW = {
    'None': 'No specific point of view restriction',
    'First person singular': 'Using I, me, my, mine - personal perspective',
    'First person plural': 'Using we, us, our, ours - collective perspective',
    'Second person': 'Using you, your, yours - direct reader address',
    'Third person': 'Using he, she, it, they - objective perspective'
}

AI_CONTENT_CLEANING = {
    'No AI Words Removal': '保持AI生成的原始内容',
    'Basic AI Words Removal': '基础清理AI特征词汇',
    'Extended AI Words Removal': '深度清理AI特征词汇和表达方式'
}

# SEO优化选项
SEO_STRATEGIES = {
    '基础优化': 'Basic SEO optimization with keywords and title optimization',
    '中度优化': 'Enhanced optimization with long-tail keywords, internal linking, and heading structure',
    '深度优化': 'Comprehensive SEO optimization including keyword placement, title optimization, and internal linking'
}

# 目标受众选项
TARGET_AUDIENCES = {
    '初学者': 'Use simple and easy-to-understand language, explain basic concepts',
    '中级用户': 'Assume basic knowledge, can use some technical terms',
    '专业人士': 'Use technical terms and in-depth content for industry experts',
    '普通大众': 'General language suitable for a broad audience',
    '决策者': 'Focus on decision-making criteria and business value'
}

# 关键词意图选项
SEARCH_INTENTS = {
    '信息型(Informational)': {
        'description': '用户寻找特定问题的答案或了解某个主题',
        'prompt': '提供详细、准确的信息，解释概念，使用示例说明',
        'patterns': [
            'How to {keyword}',
            'Guide to {keyword}',
            '{keyword} explained',
            'Understanding {keyword}',
            'What is {keyword}',
            '{keyword} tips and tricks',
            'Complete guide to {keyword}',
            '{keyword} best practices',
            '{keyword} tutorial',
            'Learn about {keyword}'
        ]
    },
    '导航型(Navigational)': {
        'description': '用户寻找特定网站或页面',
        'prompt': '提供清晰的指引和直接的信息',
        'patterns': [
            '{keyword} official website',
            '{keyword} login',
            '{keyword} download',
            'Access {keyword}',
            '{keyword} portal',
            'Find {keyword}',
            '{keyword} location'
        ]
    },
    '商业型(Commercial)': {
        'description': '用户在购买前研究产品或服务',
        'prompt': '提供客观的评估和比较，突出关键特性和优势',
        'patterns': [
            'Best {keyword}',
            'Top {keyword} reviews',
            '{keyword} comparison',
            '{keyword} alternatives',
            'Compare {keyword}',
            '{keyword} vs',
            '{keyword} pricing',
            'Review of {keyword}',
            '{keyword} features',
            'Which {keyword} to buy'
        ]
    },
    '交易型(Transactional)': {
        'description': '用户准备购买或采取行动',
        'prompt': '提供具体的行动建议和详细的操作步骤',
        'patterns': [
            'Buy {keyword}',
            '{keyword} for sale',
            'Get {keyword}',
            'Download {keyword}',
            'Purchase {keyword}',
            'Order {keyword}',
            '{keyword} discount',
            '{keyword} deals',
            'Cheap {keyword}',
            '{keyword} price'
        ]
    }
}

# 添加语言选项常量
LANGUAGES = [
    "English (US)", "English (UK)", "English (AU)",
    "简体中文", "繁體中文",
    "Español (Spanish)", "Español (Latin America)",
    "Français (French)", "Deutsch (German)",
    "Italiano (Italian)", "Português (Portuguese)",
    "Русский (Russian)", "日本語 (Japanese)",
    "한국어 (Korean)", "हिंदी (Hindi)",
    "العربية (Arabic)", "Nederlands (Dutch)",
    "Polski (Polish)", "Türkçe (Turkish)",
    "Svenska (Swedish)", "Dansk (Danish)",
    "Suomi (Finnish)", "Norsk (Norwegian)",
    "Ελληνικά (Greek)", "עברית (Hebrew)",
    "Tiếng Việt (Vietnamese)", "ไทย (Thai)",
    "Bahasa Indonesia", "Bahasa Melayu",
    "Čeština (Czech)", "Magyar (Hungarian)",
    "Română (Romanian)", "Български (Bulgarian)",
    "Hrvatski (Croatian)", "Slovenščina (Slovenian)",
    "Українська (Ukrainian)"
]

# 添加可读性级别常量
READABILITY_LEVELS = {
    "5th grade": "Simple and easy to read",
    "6th grade": "Easy to read, conversational",
    "7th grade": "Fairly easy to read",
    "8th-9th grade": "Plain English, easily understood",
    "10th-12th grade": "Fairly difficult to read"
}

def initialize_session_state():
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'title' not in st.session_state:
        st.session_state.title = ''
    if 'language' not in st.session_state:
        st.session_state.language = 'English (US)'
    if 'is_api_key_valid' not in st.session_state:
        st.session_state.is_api_key_valid = False
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'gpt-4-0125-preview'  # 设置默认模型为最新的GPT-4
    if 'generated_titles' not in st.session_state:
        st.session_state.generated_titles = []
    if 'show_title_selection' not in st.session_state:
        st.session_state.show_title_selection = False
    if 'outline' not in st.session_state:
        st.session_state.outline = ''
    if 'edited_outline' not in st.session_state:
        st.session_state.edited_outline = ''
    if 'show_outline_editor' not in st.session_state:
        st.session_state.show_outline_editor = False

def get_available_models():
    return {
        'gpt-4-0125-preview': {
            'name': 'GPT-4 Latest',
            'description': '最新版的GPT-4模型，支持更长上下文，知识库更新至2024年',
            'max_tokens': 128000,
            'cost': 'High'
        },
        'gpt-4-turbo-preview': {
            'name': 'GPT-4 Turbo',
            'description': 'GPT-4 Turbo版本，支持更长上下文和更新的知识',
            'max_tokens': 4096,
            'cost': 'Higher'
        },
        'gpt-4': {
            'name': 'GPT-4',
            'description': '强大的语言模型，适合复杂任务',
            'max_tokens': 8192,
            'cost': 'High'
        },
        'gpt-3.5-turbo': {
            'name': 'GPT-3.5 Turbo',
            'description': '高性能模型，适合大多数任务',
            'max_tokens': 4096,
            'cost': 'Low'
        }
    }

def validate_api_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        # 尝试一个简单的 API 调用来验证密钥
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hi"}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        st.error(f"API 验证错误: {str(e)}")
        print(f"API 验证详细错误: {str(e)}")
        return False

def create_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ API 设置")
        
        # API 密钥输入
        api_key = st.text_input(
            "OpenAI API 密钥",
            type="password",
            value=st.session_state.openai_api_key,
            help="输入你的 OpenAI API 密钥，以 'sk-' 开头"
        )
        
        # 验证按钮
        if st.button("验证 API 密钥"):
            if not api_key:
                st.warning("请输入 API 密钥")
            elif not api_key.startswith('sk-'):
                st.error("API 密钥格式错误，应该以 'sk-' 开头")
            else:
                with st.spinner("正在验证 API 密钥..."):
                    if validate_api_key(api_key):
                        st.session_state.openai_api_key = api_key
                        st.session_state.is_api_key_valid = True
                        st.success("✅ API 密钥验证成功！")
                    else:
                        st.session_state.is_api_key_valid = False
                        st.error("❌ API 密钥验证失败，请确保：\n1. API 密钥正确\n2. API 密钥未过期\n3. 有足够的额度")
        
        if st.session_state.is_api_key_valid:
            st.success("当前状态：API 密钥已验证 ✅")
            
            # AI 模型选择
            st.markdown("### 🤖 AI 模型设置")
            models = get_available_models()
            selected_model = st.selectbox(
                "选择 AI 模型",
                options=list(models.keys()),
                format_func=lambda x: models[x]['name'],
                index=list(models.keys()).index(st.session_state.selected_model)
            )
            
            # 显示模型信息
            if selected_model:
                st.session_state.selected_model = selected_model
                model_info = models[selected_model]
                st.markdown(f"""
                **模型信息：**
                - 描述：{model_info['description']}
                - 最大长度：{model_info['max_tokens']} tokens
                - 成本：{model_info['cost']}
                """)
        
        st.markdown("---")
        st.markdown("### 💡 使用说明")
        st.markdown("""
        1. 输入并验证你的 OpenAI API 密钥
        2. 选择合适的 AI 模型
        3. 在主界面输入博客关键词
        4. 选择文章类型和其他设置
        5. 点击生成标题和内容
        """)
        
        st.markdown("---")
        st.markdown("### 🔗 相关链接")
        st.markdown("[获取 OpenAI API 密钥](https://platform.openai.com/api-keys)")
        st.markdown("[查看使用文档](https://docs.streamlit.io)")

def get_language_settings(language):
    """获取语言的具体设置"""
    # 提取语言代码
    lang_code = language.split(" ")[0]
    
    # 特殊处理中文
    if "中文" in language:
        return {
            "word_unit": "字",
            "lang_prompt": "用简体中文" if "简体" in language else "用繁體中文"
        }
    # 特殊处理阿拉伯语
    elif "العربية" in language:
        return {
            "word_unit": "words",
            "lang_prompt": "in Arabic with right-to-left writing"
        }
    # 其他语言
    else:
        return {
            "word_unit": "words",
            "lang_prompt": f"in {lang_code}"
        }

def get_title_prompt(article_type, language):
    """根据文章类型获取标题生成提示"""
    title_patterns = {
        "How-to guide": "Create a 'How to' style title that promises to teach or guide",
        "Listicle": "Create a number-based list title (e.g. '10 Best...', '5 Ways to...')",
        "Product review": "Create a comprehensive product review title that includes the product name",
        "News": "Create a news-style headline that's current and engaging",
        "Comparison": "Create a 'X vs Y' or 'X or Y' style comparison title",
        "Case study": "Create a case study title that highlights results or insights",
        "Opinion piece": "Create an opinion piece title that's thought-provoking",
        "Tutorial": "Create a step-by-step tutorial title that's specific and actionable",
        "Roundup post": "Create a roundup style title (e.g. 'Best X of [Year]', 'Top X for Y')",
        "Q&A page": "Create a question-based title that addresses a specific query",
        "None": "Create a clear and engaging blog post title"
    }
    
    base_prompt = title_patterns.get(article_type, title_patterns["None"])
    
    # 添加语言特定的指示
    lang_settings = get_language_settings(language)
    return f"{base_prompt} {lang_settings['lang_prompt']}. The title should be SEO-friendly and compelling."

def validate_title_length(title, max_length=60):
    """验证标题长度并在需要时截断"""
    if len(title) > max_length:
        # 尝试在单词边界截断
        truncated = title[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated.strip()
    return title

def generate_title_variations(keyword, language, search_intent):
    try:
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        # 获取意图相关的标题模式
        intent_info = SEARCH_INTENTS[search_intent]
        patterns = intent_info['patterns']
        intent_desc = intent_info['description']
        
        system_prompt = f"""You are a professional title generator. Generate 5 engaging blog post titles for the given keyword.
        Requirements:
        1. Write titles in {language}
        2. Search Intent: {search_intent} - {intent_desc}
        3. Use these patterns as inspiration (but don't copy exactly): {', '.join(patterns)}
        4. Each title should:
           - Be unique and creative
           - Include the main keyword naturally
           - Match the search intent
           - Be compelling and click-worthy
           - Be between 40-60 characters
           - Use power words appropriately
        5. Avoid clickbait - titles must accurately reflect potential content
        6. Consider SEO best practices for title writing
        """

        response = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate 5 unique titles for the keyword: {keyword}"}
            ]
        )
        
        # 处理返回的标题
        titles = response.choices[0].message.content.strip().split('\n')
        # 清理标题格式（移除序号等）
        titles = [re.sub(r'^\d+\.\s*', '', title).strip() for title in titles]
        # 过滤空标题
        titles = [title for title in titles if title]
        
        return titles[:5]  # 确保只返回5个标题
    except Exception as e:
        st.error(f"生成标题时出错: {str(e)}")
        return None

def generate_outline(keyword, title, language, search_intent):
    """生成文章大纲"""
    try:
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        # 获取语言设置
        lang_settings = get_language_settings(language)
        intent_info = SEARCH_INTENTS[search_intent]
        
        system_prompt = f"""You are a professional blog outline generator. Create a detailed outline following these specifications:

1. CONTEXT:
- Title: "{title}"
- Main Keyword: "{keyword}"
- Search Intent: {search_intent} - {intent_info['description']}
- Language: {lang_settings['lang_prompt']}

2. OUTLINE STRUCTURE:
- Start with [Introduction]
- Include multiple H2 sections (marked with ##)
- Under each H2, include H3 subsections (marked with ###)
- Each H3 can have bullet points for detailed subtopics
- End with [Conclusion]

3. GUIDELINES:
- Create a logical flow of topics
- Ensure comprehensive coverage of the subject
- Include specific subtopics that address the search intent
- Make section titles clear and descriptive
- Use proper heading hierarchy (H2 -> H3 -> bullet points)
- Each section should be focused and well-structured
"""

        response = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a detailed outline for an article about '{title}' focusing on '{keyword}'. Use proper markdown formatting with ## for H2 and ### for H3 headings."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"生成大纲时出错: {str(e)}")
        return None

def parse_outline(outline):
    """解析大纲，将其分解为引言、H2部分及其子内容"""
    sections = []
    current_section = None
    current_content = []
    
    # 首先找到引言部分
    introduction_found = False
    
    for line in outline.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是引言部分
        if '[Introduction]' in line or 'Introduction' in line:
            if current_section is not None:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content)
                })
            current_section = '## Introduction'
            current_content = [current_section]
            introduction_found = True
        # 识别H2标题
        elif line.startswith('## ') or line.startswith('**[H2]'):
            if current_section is not None:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content)
                })
            # 清理H2标题格式
            clean_title = line.replace('**[H2]', '## ').replace('**', '')
            if not clean_title.startswith('## '):
                clean_title = '## ' + clean_title
            current_section = clean_title
            current_content = [clean_title]
        # 收集当前部分下的所有内容
        elif current_section is not None:
            # 清理H3标题格式
            if line.startswith('- [H3]'):
                line = '### ' + line.replace('- [H3]', '').strip()
            elif line.startswith('- '):
                line = line.strip()
            current_content.append(line)
    
    # 添加最后一个部分
    if current_section is not None:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content)
        })
    
    return sections

def parse_outline_sections(outline):
    """解析大纲，将其分解为可选择的H2部分"""
    sections = []
    current_section = None
    current_content = []
    
    for line in outline.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # 识别H2标题
        if line.startswith('## ') or line.startswith('**[H2]'):
            # 保存之前的部分（如果存在）
            if current_section is not None:
                sections.append({
                    'title': current_section,
                    'content': current_content,
                    'selected': False  # 添加选择状态
                })
            # 清理H2标题格式
            clean_title = line.replace('**[H2]', '').replace('**', '').strip()
            if not clean_title.startswith('## '):
                clean_title = '## ' + clean_title
            current_section = clean_title
            current_content = []
        # 收集H2下的所有内容（H3和H4）
        elif current_section is not None:
            # 清理H3标题格式
            if line.startswith('- [H3]'):
                line = '### ' + line.replace('- [H3]', '').strip()
            elif line.startswith('- '):
                line = line.strip()
            current_content.append(line)
    
    # 添加最后一个部分
    if current_section is not None:
        sections.append({
            'title': current_section,
            'content': current_content,
            'selected': False
        })
    
    return sections

def generate_article_content(outline, context):
    """生成文章内容"""
    try:
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        # 获取语言设置和搜索意图信息
        lang_settings = get_language_settings(context['language'])
        intent_info = SEARCH_INTENTS[context['search_intent']]
        
        system_prompt = f"""You are a professional blog writer. Write content based on the provided outline and context:

1. CONTEXT:
- Title: "{context['title']}"
- Main Keyword: "{context['keyword']}"
- Search Intent: {context['search_intent']} - {intent_info['prompt']}
- Language: {lang_settings['lang_prompt']}
- Tone of Voice: {TONE_OF_VOICE[context['tone_of_voice']]}
- Point of View: {POINT_OF_VIEW[context['pov']]}
- Content Cleaning: {AI_CONTENT_CLEANING[context['content_cleaning']]}
- Readability: {READABILITY_LEVELS[context['readability']]}
- Article Size: {ARTICLE_SIZES[context['article_size']]['description']}

2. GUIDELINES:
- Write naturally and engagingly
- Maintain consistent tone and style
- Use appropriate examples and explanations
- Format text with proper markdown
- Ensure content matches the search intent
- Follow the outline structure exactly
- Generate content for EACH heading in the outline
- Keep the heading hierarchy (## for H2, ### for H3)
- Include relevant examples and details under each section

3. OUTLINE:
{outline}

Remember to:
1. Generate content for each section in the outline
2. Maintain the heading structure
3. Make the content flow naturally between sections
4. Keep the content focused and relevant to each heading
"""

        response = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Write detailed content for each section in the outline, maintaining the heading structure and ensuring good flow between sections."}
            ],
            temperature=0.7,
            max_tokens=3500
        )
        
        # 获取生成的内容
        content = response.choices[0].message.content
        
        # 如果内容不是以标题开始，添加标题
        if not content.startswith('#'):
            content = f"# {context['title']}\n\n{content}"
            
        return content
    except Exception as e:
        st.error(f"生成内容时出错: {str(e)}")
        return None

def main():
    initialize_session_state()
    
    # 创建侧边栏
    create_sidebar()
    
    # 添加自定义CSS样式
    st.markdown("""
        <style>
        /* 按钮对齐样式 */
        div.stButton > button {
            height: 45px;
            margin-top: 24px;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
        }
        
        /* 标题选择区域样式 */
        div.stRadio > div {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            background-color: #f0f2f6;
            transition: all 0.3s ease;
            width: 100% !important;
        }
        
        div.stRadio > div:hover {
            background-color: #e8eaf6;
        }
        
        /* 选中状态的样式 */
        div.stRadio > div[data-baseweb="radio"] > div {
            background-color: #4CAF50 !important;
        }
        
        /* 标题选择区容器 */
        .title-selection-container {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
            width: 100% !important;
        }
        
        /* 标题选择标题样式 */
        .title-selection-header {
            width: 100% !important;
            text-align: left;
            margin-bottom: 20px;
            color: #333;
        }
        
        /* 确保radio选项占满宽度 */
        .stRadio [role="radiogroup"] {
            width: 100% !important;
        }
        
        .stRadio [role="radio"] {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 AI 博客写作助手")
    st.markdown("谷歌SEO写作工具，微信:8845665 后续会持续更新")

    if not st.session_state.is_api_key_valid:
        st.warning("请先在侧边栏设置并验证 API 密钥")
        return

    # 使用容器来组织布局
    with st.container():
        # 关键词输入区域
        st.subheader("1️⃣ 输入关键词")
        
        # 使用columns来确保输入框和按钮在同一行
        keyword_col1, keyword_col2 = st.columns([4, 1])
            
        with keyword_col1:
            keyword = st.text_input(
                "主要关键词",
                help="输入你想要写作的主题关键词",
                placeholder="例如：plastic recycling machine",
                key="keyword_input",
                label_visibility="visible"
            )
        with keyword_col2:
            confirm_keyword = st.button(
                "确认关键词 ✅",
                use_container_width=True,
                type="primary"
            )
        
        # 标题生成区域
        if confirm_keyword and keyword:
            st.session_state.confirmed_keyword = keyword
            st.session_state.show_title_options = True
        
        if getattr(st.session_state, 'show_title_options', False):
            st.subheader("2️⃣ 生成标题")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                language = st.selectbox(
                    "选择语言",
                    LANGUAGES,
                    help="选择文章的目标语言"
                )
            with col2:
                search_intent = st.selectbox(
                    "关键词意图",
                    list(SEARCH_INTENTS.keys()),
                    help="选择关键词的意图"
                )
            with col3:
                generate_titles = st.button("生成标题建议", type="primary", use_container_width=True)
                
            if generate_titles:
                with st.spinner("正在生成标题建议..."):
                    titles = generate_title_variations(
                        st.session_state.confirmed_keyword,
                        language,
                        search_intent
                    )
                    if titles:
                        st.session_state.generated_titles = titles
                        st.session_state.show_title_selection = True

            # 如果已经生成了标题，显示选择区域
            if st.session_state.show_title_selection and st.session_state.generated_titles:
                st.markdown("---")
                st.markdown('<div class="title-selection-header"><h3>🎯 请选择一个标题</h3></div>', unsafe_allow_html=True)
                st.markdown('<div class="title-selection-container">', unsafe_allow_html=True)
                selected_title = st.radio(
                    "",
                    st.session_state.generated_titles,
                    label_visibility="collapsed",
                    key="title_selection"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if selected_title:
                    st.session_state.title = selected_title
                    st.success(f"已选择标题：{selected_title}")

                    # 生成大纲按钮
                    if st.button("✨ 生成文章大纲", type="primary", key="generate_outline"):
                        if st.session_state.confirmed_keyword and st.session_state.title:
                            with st.spinner("正在生成大纲..."):
                                # 生成大纲
                                outline = generate_outline(
                                    st.session_state.confirmed_keyword,
                                    st.session_state.title,
                                    language,
                                    search_intent
                                )
                                
                                if outline:
                                    # 保存生成的大纲
                                    st.session_state.generated_outline = outline
                                    st.session_state.show_outline_editor = True
                                    # 清除之前的选择
                                    if 'outline_content' in st.session_state:
                                        del st.session_state.outline_content
                                    
                                    # 显示生成的大纲
                                    st.success("✅ 大纲生成完成！")
                                    st.markdown("### 📋 生成的大纲")
                                    st.markdown(outline)
                                    
                                    # 提示用户如何选择部分
                                    st.info("👆 现在您可以选择要生成的部分。在要生成的段落前添加 > 符号，例如：\n```\n> ## 引言\n## 第二部分\n> ## 第三部分\n```")
                        else:
                            st.error("请先输入关键词和选择标题")

                    # 如果已经生成了大纲，显示选择界面
                    if st.session_state.show_outline_editor:
                        st.markdown("### 📑 大纲选择")
                        st.markdown("选择要生成的部分")
                        
                        # 解析大纲为可选择的部分
                        if 'outline_sections' not in st.session_state:
                            st.session_state.outline_sections = []
                            current_section = None
                            for line in st.session_state.generated_outline.split('\n'):
                                if line.strip().startswith('##'):
                                    if current_section:
                                        st.session_state.outline_sections.append(current_section)
                                    current_section = {
                                        'title': line.strip(),
                                        'content': [],
                                        'selected': False
                                    }
                                elif current_section and line.strip():
                                    current_section['content'].append(line.strip())
                            if current_section:
                                st.session_state.outline_sections.append(current_section)
                        
                        # 创建列布局用于全选/取消全选按钮
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("全选", key="select_all"):
                                for section in st.session_state.outline_sections:
                                    section['selected'] = True
                        with col2:
                            if st.button("取消全选", key="deselect_all"):
                                for section in st.session_state.outline_sections:
                                    section['selected'] = False
                        
                        # 显示每个部分的选择框
                        st.markdown("#### 选择要生成的部分：")
                        for i, section in enumerate(st.session_state.outline_sections):
                            container = st.container()
                            # 使用 checkbox 来选择部分
                            selected = container.checkbox(
                                section['title'].strip('# '),
                                key=f"section_{i}",
                                value=section.get('selected', False)
                            )
                            # 更新选择状态
                            section['selected'] = selected
                            
                            # 显示子标题
                            if section['content']:
                                with container.expander("查看子标题"):
                                    st.markdown('\n'.join(f"- {item}" for item in section['content']))

                        # 文章生成选项
                        st.markdown("### ⚙️ 生成选项")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            tone_of_voice = st.selectbox(
                                "语气风格",
                                options=list(TONE_OF_VOICE.keys()),
                                help="选择文章的语气和风格",
                                key="tone_select"
                            )
                            
                            pov = st.selectbox(
                                "视角",
                                options=list(POINT_OF_VIEW.keys()),
                                help="选择文章的叙述视角",
                                key="pov_select"
                            )

                        with col2:
                            content_cleaning = st.selectbox(
                                "AI内容优化",
                                options=list(AI_CONTENT_CLEANING.keys()),
                                help="选择AI生成内容的优化程度",
                                key="cleaning_select"
                            )
                            
                            article_size = st.selectbox(
                                "段落长度",
                                options=list(ARTICLE_SIZES.keys()),
                                format_func=lambda x: f"{x} ({ARTICLE_SIZES[x]['tokens_per_section']} tokens/段落)",
                                help="选择每个段落的平均长度",
                                key="size_select"
                            )

                        readability = st.selectbox(
                            "可读性级别",
                            options=list(READABILITY_LEVELS.keys()),
                            index=3,  # 默认选择8th-9th grade
                            help="选择文章的可读性级别，影响语言的复杂程度",
                            key="readability_select"
                        )
                        
                        # 生成选中部分的按钮
                        if st.button("✨ 生成选中的部分", type="primary", key="generate_selected"):
                            # 获取选中的部分
                            selected_sections = [
                                section for section in st.session_state.outline_sections 
                                if section['selected']
                            ]
                            
                            if not selected_sections:
                                st.warning("请至少选择一个部分来生成内容")
                            else:
                                try:
                                    # 构建选中部分的大纲
                                    selected_outline = "# " + st.session_state.title + "\n\n"  # 添加文章标题
                                    for section in selected_sections:
                                        # 添加主标题
                                        selected_outline += f"{section['title']}\n"
                                        # 添加子内容
                                        if section['content']:
                                            selected_outline += "\n".join(section['content']) + "\n\n"
                                    
                                    # 创建上下文字典
                                    context = {
                                        'keyword': st.session_state.confirmed_keyword,
                                        'title': st.session_state.title,
                                        'language': language,
                                        'search_intent': search_intent,
                                        'tone_of_voice': tone_of_voice,
                                        'pov': pov,
                                        'content_cleaning': content_cleaning,
                                        'readability': readability,
                                        'article_size': article_size
                                    }
                                    
                                    # 创建容器
                                    article_container = st.container()
                                    with article_container:
                                        st.markdown("### 📝 生成的内容")
                                        
                                        # 显示生成状态
                                        status_text = st.empty()
                                        status_text.text("正在生成内容...")
                                        
                                        # 生成选中部分的内容
                                        article_content = generate_article_content(
                                            selected_outline,
                                            context
                                        )
                                        
                                        if article_content:
                                            # 显示生成的内容
                                            st.markdown(article_content)
                                            # 保存到session state
                                            st.session_state['article_content'] = article_content
                                            # 更新状态
                                            status_text.text("✨ 内容生成完成！")
                                        else:
                                            st.error("内容生成失败，请重试。")
                                except Exception as e:
                                    st.error(f"生成内容时出错: {str(e)}")
                                    st.write("错误详情：", e)

if __name__ == "__main__":
    main()
