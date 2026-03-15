import streamlit as st
import pandas as pd
import threading

# 页面配置 - 放在最前面
st.set_page_config(
    page_title="糖尿病饮食计算器",
    page_icon="🍚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 设置页面样式
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .main > div {
        padding: 2rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 标题
st.title("🍚 糖尿病饮食计算器")
st.markdown("---")

# 创建两列布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 输入参数")
    
    # 输入控件
    carb_factor = st.number_input(
        "碳水系数 (克/单位)", 
        min_value=0.1, 
        max_value=100.0, 
        value=11.0,
        step=0.5,
        help="每单位胰岛素可以处理的碳水化合物克数",
        key="carb_factor"
    )
    
    correction_factor = st.number_input(
        "纠正值 (mmol/L/单位)", 
        min_value=0.1, 
        max_value=10.0, 
        value=1.2,
        step=0.1,
        help="每单位胰岛素可以降低的血糖值",
        key="correction_factor"
    )
    
    insulin_dose = st.number_input(
        "胰岛素药量 (单位)", 
        min_value=0.5, 
        max_value=50.0, 
        value=6.0,
        step=0.5,
        key="insulin_dose"
    )

with col2:
    st.subheader("🩸 血糖参数")
    
    pre_meal_glucose = st.number_input(
        "餐前血糖 (mmol/L)", 
        min_value=0.0, 
        max_value=30.0, 
        value=8.5,
        step=0.1,
        key="pre_meal_glucose"
    )
    
    carb_ratio = st.number_input(
        "主食碳水占比 (%)", 
        min_value=1.0, 
        max_value=100.0, 
        value=30.0,
        step=0.1,
        help="主食中碳水化合物占总碳水的百分比",
        key="carb_ratio"
    )
    
    # 显示血糖范围提示
    st.info("🩺 血糖正常范围：6.5 - 7.0 mmol/L")

st.markdown("---")

# 创建计算按钮和结果显示
if st.button("🧮 计算主食质量", type="primary", use_container_width=True):
    try:
         # 计算血糖调整值
        if pre_meal_glucose < 6.5:
            adjustment = pre_meal_glucose - 6.5
            status = "偏低 ⬇️"
            status_icon = "🔴"
        elif pre_meal_glucose > 14:
            adjustment = pre_meal_glucose - 8
            status = "极高 ⬆️⬆️"
            status_icon = "🔴"  # 或使用 "🔥"
        elif pre_meal_glucose > 7:
            adjustment = pre_meal_glucose - 7
            status = "偏高 ⬆️"
            status_icon = "🟡"
        else:
            adjustment = 0
            status = "正常 ✅"
            status_icon = "🟢"
        
        # 计算主食质量
        numerator = (insulin_dose * carb_factor) - (adjustment * correction_factor)
        
        # 显示结果
        st.markdown("### 📈 计算结果")
        
        # 创建三列显示中间结果
        res_col1, res_col2, res_col3 = st.columns(3)
        
        with res_col1:
            st.metric("血糖状态", status, status_icon)
        
        with res_col2:
            st.metric("血糖调整值", f"{adjustment:.2f} mmol/L")
        
        # 判断计算结果
        if numerator < 0:
            with res_col3:
                st.metric("分子结果", f"{numerator:.2f}", delta="-", delta_color="inverse")
            
            st.error("⚠️ **计算结果为负值！**")
            st.warning("""
            **可能的原因和建议：**
            - 胰岛素剂量过高，可以适当减少
            - 血糖值偏低，可以先吃点东西再注射
            - 纠正值设置可能偏大
            """)
        else:
            food_weight = numerator / (carb_ratio / 100)
            
            with res_col3:
                st.metric("分子结果", f"{numerator:.2f}")
            
            # 显示主要结果
            st.success(f"### 🍽️ 推荐主食质量：**{food_weight:.1f} 克**")
            
            # 换算参考
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info(f"📊 约 {food_weight/100:.1f} 两")
            with col_b:
                st.info(f"📊 约 {food_weight/50:.1f} 份")
            with col_c:
                st.info(f"📊 约 {food_weight/15:.1f} 勺")
            
            # 添加进度条可视化
            progress_value = min(food_weight/300, 1.0)  # 假设最大300克
            st.progress(progress_value, text=f"相对份量: {progress_value*100:.0f}%")
            
    except Exception as e:
        st.error(f"计算过程中出现错误：{str(e)}")

# 添加历史记录功能（可选）
st.markdown("---")
with st.expander("📜 最近计算记录"):
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    # 保存当前计算
    col_save1, col_save2 = st.columns([1, 3])
    with col_save1:
        if st.button("💾 保存本次计算"):
            if 'food_weight' in locals():
                record = {
                    '时间': pd.Timestamp.now().strftime('%H:%M'),
                    '血糖': f"{pre_meal_glucose:.1f}",
                    '胰岛素': f"{insulin_dose:.1f}",
                    '主食': f"{food_weight:.0f}g"
                }
                st.session_state.history.append(record)
                st.success("✓ 已保存")
            else:
                st.warning("请先进行计算")
    
    # 显示历史记录
    if st.session_state.history:
        # 转换为DataFrame显示
        history_df = pd.DataFrame(st.session_state.history)
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 清空历史按钮
        if st.button("🗑️ 清空历史"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("暂无历史记录")

# 底部说明
st.markdown("---")
with st.expander("📖 详细使用说明", expanded=False):
    col_help1, col_help2 = st.columns(2)
    
    with col_help1:
        st.markdown("""
        **📝 计算公式：**
        1. 餐前血糖 5-7 mmol/L：调整值 = 0
        2. 餐前血糖 > 7 mmol/L：调整值 = 血糖 - 7
        3. 餐前血糖 < 5 mmol/L：调整值 = 血糖 - 5
        
        **主食质量 = (胰岛素 × 碳水系数 - 调整值 × 纠正值) ÷ (碳水占比 ÷ 100)**
        """)
    
    with col_help2:
        st.markdown("""
        **🔄 换算参考：**
        - 1两 = 50克
        - 1份主食 ≈ 15克碳水
        - 1勺 ≈ 15克米饭
        - 1碗 ≈ 150克米饭
        """)

# 页脚
st.markdown("---")
st.caption("© 2026 糖尿病饮食计算器 | 计算结果仅供参考，具体用药请遵医嘱")
