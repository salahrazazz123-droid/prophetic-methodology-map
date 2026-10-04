import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import os
import time

# ═══════════════════════════════════════════════════════
# إعدادات الصفحة
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="نظام استكشاف منهج النبي ﷺ",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Cairo', sans-serif;
    }
    .main-title {
        background: linear-gradient(135deg, #0d4d3d 0%, #1a6b52 100%);
        color: white; padding: 25px; border-radius: 14px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .main-title h1 { margin: 0; font-size: 24px; }
    .main-title p { margin: 8px 0 0 0; font-size: 15px; opacity: 0.9; }
    .idea-box {
        background: #f8f9fa; border-right: 5px solid #0d4d3d;
        border-radius: 10px; padding: 20px; margin: 15px 0; line-height: 1.9;
    }
    .important-box {
        background: linear-gradient(135deg, #0d4d3d 0%, #1a6b52 100%);
        color: white; padding: 25px; border-radius: 14px; margin: 20px 0;
        font-size: 17px; line-height: 2; border: 3px solid #d4af37;
    }
    .important-box h3 { color: #d4af37; margin-top: 0; font-size: 21px; }
    .warning-box {
        background: #fff3cd; border-right: 5px solid #ffc107;
        border-radius: 10px; padding: 15px; margin: 15px 0; color: #856404;
    }
    .step-card {
        background: #f8f9fa; border-right: 4px solid #d4af37;
        border-radius: 10px; padding: 18px; margin: 12px 0; line-height: 1.9;
    }
    .step-card h4 { color: #0d4d3d; margin-top: 0; }
    .example-box {
        background: #e8f0ec; padding: 12px; border-radius: 8px; margin: 10px 0;
    }
    /* بطاقات تفكير/شعور/تصرف */
    .tf-box {
        border-radius: 10px; padding: 14px; margin: 8px 0; line-height: 1.8;
    }
    .tf-think { background: #e7f3ff; border-right: 5px solid #2b7bbf; }
    .tf-feel  { background: #fdeef3; border-right: 5px solid #c25e8a; }
    .tf-act   { background: #e8f6ee; border-right: 5px solid #2e9e63; }
    /* الخريطة المدمجة (شريط تنقل) */
    .center-mini {
        background: linear-gradient(135deg, #d4af37, #b8941e);
        color: #0d4d3d; padding: 10px 20px; border-radius: 30px;
        text-align: center; font-weight: bold; font-size: 15px;
        border: 3px solid #0d4d3d; display: inline-block; margin: 5px;
    }
    .trunk-mini {
        background: linear-gradient(135deg, #0d4d3d, #1a6b52);
        color: white; padding: 10px 20px; border-radius: 10px;
        text-align: center; font-weight: bold; font-size: 13px;
        display: inline-block; margin: 5px;
    }
    .dim-num {
        font-size: 42px; font-weight: bold; color: #d4af37;
        line-height: 1;
    }
    .golden-summary {
        background: linear-gradient(135deg, #0d4d3d, #1a6b52);
        color: white; padding: 20px; border-radius: 12px;
        text-align: center; margin: 15px 0; font-size: 17px; font-weight: bold;
        border: 3px solid #d4af37;
    }
    .hadith-card {
        background: white; border: 1px solid #ddd; border-right: 5px solid #0d4d3d;
        border-radius: 10px; padding: 15px; margin: 10px 0; line-height: 1.8;
    }
    .source-tag {
        background: #0d4d3d; color: white; padding: 4px 12px;
        border-radius: 15px; font-size: 13px; display: inline-block;
    }
    .disclaimer {
        background: #fff3cd; border-right: 4px solid #ffc107;
        padding: 12px; border-radius: 8px; margin-top: 20px; color: #856404; font-size: 14px;
    }
    /* جعل شريط التنقل العلوي مريحاً للعربية */
    [data-testid="stNavigation"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# الأبعاد العشرة — كيف كان يفكر ويشعر ويتصرف ﷺ
# ═══════════════════════════════════════════════════════
DIMENSIONS = [
    {
        "id": 1, "name": "المعرفة", "question": "كيف نعرف؟ وما مصدر علمنا؟", "icon": "📖",
        "definition": "المعرفة هي: كيف نعرف؟ من أين نأخذ علمنا؟ كيف نتعلم؟ كيف نعلم؟",
        "importance": "لأن كل شيء يبدأ من المعرفة. إذا صحت ← صح كل شيء. وإذا فسدت ← فسد كل شيء.",
        "think": "من الوحي أولًا، ثم بالمقاصد، ثم بالمشورة.",
        "feel": "يشعر بالمسؤولية، وبالشوق إلى المعرفة، وبالرضا عند تحقيقها.",
        "act": "يتعلم، ويعلم، ويراجع، ويعمل بعلمه.",
        "evidence": "«وما ينطق عن الهوى إن هو إلا وحي يوحى» (النجم 3-4) • «وشاورهم في الأمر» (آل عمران 159)",
        "constants": [
            {"name": "الوحي", "desc": "مصدر المعرفة الأعلى", "evidence": "«وما ينطق عن الهوى»"},
            {"name": "العقل", "desc": "أداة للفهم لا للتشريع", "evidence": "«أفلا تعقلون»"},
            {"name": "الصدق في النقل", "desc": "لا ننقل إلا ما ثبت", "evidence": "«من كذب علي متعمدًا»"},
            {"name": "طلب العلم", "desc": "العلم عبادة وفريضة", "evidence": "«طلب العلم فريضة»"},
            {"name": "العمل بالعلم", "desc": "شرط لقبول العلم", "evidence": "«من عمل بما علم»"},
            {"name": "التجربة والمشاهدة", "desc": "معتبرة في الأمور التجريبية", "evidence": "«رأيت» و«سمعت»"},
            {"name": "الشورى", "desc": "في المعرفة الجزئية", "evidence": "«وشاورهم في الأمر»"},
        ],
        "variables": [
            {"name": "طريقة التعليم", "desc": "حفظ، كتابة، سؤال، قصة", "serves": "طلب العلم"},
            {"name": "اللغة", "desc": "عربية أو غيرها", "serves": "فهم الوحي"},
            {"name": "الأدوات", "desc": "كتاب، هاتف، حاسوب، ذكاء اصطناعي", "serves": "طلب العلم"},
            {"name": "التخصص", "desc": "فقه، حديث، تفسير", "serves": "الشورى"},
            {"name": "المستوى", "desc": "كل يُخاطب على قدره", "serves": "الفهم"},
            {"name": "المكان", "desc": "مسجد، بيت، جامعة، إنترنت", "serves": "طلب العلم"},
            {"name": "الوقت", "desc": "صباح، مساء، سفر", "serves": "طلب العلم"},
            {"name": "المنهجية", "desc": "أصول الفقه، المصطلح", "serves": "فهم الوحي"},
            {"name": "المرجعية", "desc": "مذهب، شيخ، لجنة", "serves": "الشورى"},
            {"name": "الاختبار", "desc": "سؤال، مراجعة، تجربة", "serves": "العمل بالعلم"},
        ],
        "central_constant": "الوحي", "rule": "الوحي ثابت. طرق نقله وفهمه متغيرة.",
        "example": {"hadith": "إنما الأعمال بالنيات", "analysis": "الثابت: النية شرط. المتغير: كيف نستحضرها؟"},
        "benefit": "لا نقدّس الفهم البشري، ولا نهمل الوحي.", "goal": "الفهم الصحيح"
    },
    {
        "id": 2, "name": "القول", "question": "ماذا نقول؟ وكيف نتكلم؟", "icon": "💬",
        "definition": "القول هو: ماذا نقول؟ كيف نتكلم؟ متى نصمت؟",
        "importance": "لأن اللسان أكثر ما يدخل الناس النار، والكلمة ترفع أو تخفض.",
        "think": "هل الكلام خير؟ هل هو صحيح؟ هل هو نافع؟",
        "feel": "يشعر بالرحمة بالمخاطب، وبالمسؤولية عن كلمته، وبالحب في النصح.",
        "act": "يتكلم بوضوح، وبقلة، وبحكمة، ويصمت عند الحاجة.",
        "evidence": "«فليقل خيرًا أو ليصمت» (بخاري 6018) • «كان كلامه فصلًا» (أبو داود 4839)",
        "constants": [
            {"name": "الصدق", "desc": "لا كذب أبدًا", "evidence": "«الصدق يهدي إلى البر»"},
            {"name": "عدم الغيبة", "desc": "لا سوء في الغيبة", "evidence": "«لا يغتاب بعضكم بعضًا»"},
            {"name": "خير أو صمت", "desc": "كلام بلا خير ممنوع", "evidence": "«فليقل خيرًا أو ليصمت»"},
            {"name": "الوضوح", "desc": "لا غموض", "evidence": "«كان كلامه فصلًا»"},
            {"name": "عدم الإطالة", "desc": "بقدر الحاجة", "evidence": "«كان كلامه فصلًا»"},
            {"name": "ذكر الله", "desc": "اللسان رطب بالذكر", "evidence": "«رطبًا بذكر الله»"},
            {"name": "لا كذب ولو مازحًا", "desc": "المزاح لا يبرر الكذب", "evidence": "«ولا أقول إلا حقًا»"},
        ],
        "variables": [
            {"name": "اللغة واللهجة", "desc": "فصحى أو عامية", "serves": "الوضوح"},
            {"name": "الأسلوب", "desc": "مباشر، قصة، مثل", "serves": "الوضوح"},
            {"name": "الصوت", "desc": "رفع، خفض، همس", "serves": "الوضوح"},
            {"name": "الوقت", "desc": "صباح، مساء", "serves": "قول الخير"},
            {"name": "الجمهور", "desc": "عالم، طفل، عدو", "serves": "قول الخير"},
            {"name": "الموضوع", "desc": "عقيدة، فقه، أخلاق", "serves": "الصدق"},
            {"name": "الطول", "desc": "قصير، متوسط", "serves": "عدم الإطالة"},
            {"name": "النبرة", "desc": "حنان، حزم", "serves": "الوضوح"},
            {"name": "الوسيلة", "desc": "كلام، كتابة", "serves": "الوضوح"},
            {"name": "المكان", "desc": "مسجد، سوق", "serves": "قول الخير"},
        ],
        "central_constant": "الصدق", "rule": "الصدق ثابت. الأسلوب متغير.",
        "example": {"hadith": "فليقل خيرًا أو ليصمت", "analysis": "الثابت: خير أو صمت. المتغير: ما الخير في كل موقف؟"},
        "benefit": "نعرف متى نتكلم ومتى نصمت.", "goal": "الكلام الطيب"
    },
    {
        "id": 3, "name": "الفعل", "question": "ماذا نفعل؟ وكيف نعمل؟", "icon": "⚙️",
        "definition": "الفعل هو: ماذا نفعل؟ كيف نعمل؟ كيف نتقن؟",
        "importance": "لأن الدين عمل لا كلام فقط، وعمله ﷺ أبلغ من كلامه.",
        "think": "هل العمل لله؟ هل هو متقن؟ هل هو في وقته؟",
        "feel": "يشعر بالمسؤولية، وبالرضا بالجودة، وبالتوكل على الله.",
        "act": "يعمل بجد، ويُتقن، ويستمر، ويأخذ بالأسباب.",
        "evidence": "«أن يتقنه» (جامع 1880) • «أدومها وإن قل» (بخاري 6464)",
        "constants": [
            {"name": "الإتقان", "desc": "عمل بجودة", "evidence": "«أن يتقنه»"},
            {"name": "المبادرة", "desc": "لا تسويف", "evidence": "«بادروا بالأعمال»"},
            {"name": "الاستمرارية", "desc": "الدائم وإن قل", "evidence": "«أدومها وإن قل»"},
            {"name": "عدم الإسراف", "desc": "لا غلو ولا تقصير", "evidence": "«ولا تسرفوا»"},
            {"name": "خدمة الآخرين", "desc": "النفع عبادة", "evidence": "«أنفعهم للناس»"},
            {"name": "عدم الكسل", "desc": "استعاذة من العجز", "evidence": "«من العجز والكسل»"},
            {"name": "التوكل بعد الأخذ", "desc": "أسباب + توكل", "evidence": "«اعقلها وتوكل»"},
        ],
        "variables": [
            {"name": "نوع العمل", "desc": "عبادة، مهنة، تعليم", "serves": "الإتقان"},
            {"name": "الوقت", "desc": "ليل، نهار، سفر", "serves": "المبادرة"},
            {"name": "القدرة", "desc": "كل حسب طاقته", "serves": "الاستمرارية"},
            {"name": "الأدوات", "desc": "قلم، هاتف، آلة", "serves": "الإتقان"},
            {"name": "المكان", "desc": "بيت، عمل", "serves": "الإتقان"},
            {"name": "الطريقة", "desc": "يدوي، آلي، جماعي", "serves": "الإتقان"},
            {"name": "المقدار", "desc": "قليل، كثير", "serves": "عدم الإسراف"},
            {"name": "الشكل", "desc": "منظم، مرحلي", "serves": "الإتقان"},
            {"name": "الجمهور", "desc": "علني، سري", "serves": "خدمة الآخرين"},
            {"name": "النتيجة", "desc": "نجاح، فشل، إعادة", "serves": "الاستمرارية"},
        ],
        "central_constant": "الإتقان", "rule": "الإتقان ثابت. نوع العمل متغير.",
        "example": {"hadith": "اعقلها وتوكل", "analysis": "الثابت: أسباب + توكل. المتغير: ما الأسباب في كل عصر؟"},
        "benefit": "نجمع بين العمل والاعتماد على الله.", "goal": "العمل الصالح"
    },
    {
        "id": 4, "name": "الذات", "question": "كيف نتعامل مع أنفسنا؟", "icon": "🪞",
        "definition": "الذات هي: من نحن؟ كيف نحاسب أنفسنا؟ كيف نزكيها؟",
        "importance": "لأن إصلاح النفس أول خطوة لإصلاح المجتمع.",
        "think": "أنا عبد الله، ورسوله، وبشر، ومسؤول، وفقير إليه.",
        "feel": "يشعر بالتواضع، وبالخوف، وبالرجاء، وبالحب، وبالسكينة.",
        "act": "يحاسب نفسه، ويزكيها، ويعبد ربه، ويستغفر، ويتوب.",
        "evidence": "«أستغفر الله مائة مرة» (مسلم 2702) • «من تواضع لله رفعه الله» (مسلم 2588)",
        "constants": [
            {"name": "معرفة الله أولًا", "desc": "أصل كل شيء", "evidence": "«من عرف نفسه»"},
            {"name": "الإخلاص", "desc": "العمل لله وحده", "evidence": "«الأعمال بالنيات»"},
            {"name": "محاسبة النفس", "desc": "مراجعة دائمة", "evidence": "«حاسبوا أنفسكم»"},
            {"name": "التواضع", "desc": "لا كبر", "evidence": "«رفعه الله»"},
            {"name": "عدم العجب", "desc": "لا تزكية ذات", "evidence": "«لا تزكوا أنفسك
