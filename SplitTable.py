import streamlit as st
import pandas as pd
import os
import re
import io
import zipfile


def is_valid_path(path):
    """
    检查路径是否合法
    :param path: 需要检查的路径
    :return: 如果路径合法，返回True，否则返回False
    """
    # 检查路径是否为空
    if not path:
        return False

    # Windows路径验证
    if os.name == 'nt':
        # 检查Windows路径是否有合法的盘符开头，且不要求双反斜杠
        windows_pattern = r'^[a-zA-Z]:\\'
        return re.match(windows_pattern, path) is not None
    # OSX路径验证
    elif os.name == 'posix':
        # 检查OSX路径是否以正斜杠开头
        osx_pattern = r'^/([^/:*?"<>|\r\n]+/)*[^/:*?"<>|\r\n]*$'
        return re.match(osx_pattern, path) is not None

@st.cache_resource
def read_table_file(file_path):
    """
    读取表格文件的函数。

    参数:
    file_path (str): 表格文件的路径。

    返回:
    df (DataFrame): 读取的数据。

    """
    # 确保文件指针在开始位置
    file_path.seek(0)

    # 将文件扩展名转换为小写，以便处理大写扩展名
    file_extension = file_path.name.split('.')[-1].lower()

    # 根据文件的扩展名，使用不同的函数读取数据
    if file_extension == 'csv':
        df = pd.read_csv(file_path)
    elif file_extension in ['xls', 'xlsx']:
        df = pd.read_excel(file_path)

    return df

def convert_long_digit_cols_to_str(df, digit_limit=10):
    """
    将 DataFrame 中的长整数列转换为字符串类型。

    参数:
    df (DataFrame): 输入的 DataFrame。
    digit_limit (int): 数字长度的阈值，默认为 10。

    返回:
    long_digit_cols (list): 被转换为字符串类型的列名列表。

    """
    # 判断df中，有哪几个列中,只有整数，且最长的数字超过digit_limit位
    long_digit_cols = df.select_dtypes(include='int64').applymap(lambda x: len(str(x))).max() > digit_limit
    long_digit_cols = long_digit_cols[long_digit_cols].index.tolist()

    # 将这几个数字列的列名转为字符串类型
    df[long_digit_cols] = df[long_digit_cols].astype(str)

    # 将这几个列名存为列名列表
    long_digit_cols = df[long_digit_cols].columns.tolist()

    return long_digit_cols

def main():

    # 设置标题为“拆分表格”
    st.title('拆分表格')

    # 设置H3标题为“文件设置”
    st.subheader('文件设置')

    # 设置文件上传的按钮
    excel_path = st.file_uploader("选择需拆分的Excel、csv文件", type=['xlsx', 'xls', 'csv'])

    # 如果excel_path不为空时，则读取excel
    if excel_path:

        # 读取excel
        # 以字符串方式读取指定列名


        # 基于文件后缀，读取表格
        df = read_table_file(excel_path)

        # 将列名存为列表
        col_names = df.columns.tolist()

        "---"
        st.subheader('Excel数据预览（前3行）')
        st.dataframe(df.head(3), hide_index=True)

        "---"
        # 设置H2标题为“拆分设置”
        st.subheader('拆分设置')

        # # 通过多选框选择需要以字符串方式读取的列名
        # str_col_names = st.multiselect('需要以字符串方式读取的列名(避免出现身份证号、银行卡号等被科学计数法)', col_names)


        # 设置两个st.columns
        col3, col4 = st.columns(2)

        with col3:
            # 通过单选框选择结束列，必填
            end_col = st.selectbox('结束列(此后的列不会被拆分并输出)', col_names, index=None)

        with col4:
            # 通过单选框选择拆分依据列
            group_col = st.selectbox('拆分分组依据列(拆分时的分组依据)', col_names, index=None)

        # 增加间距
        st.write('')
        st.write('')


        # 提交按钮
        if st.button('提交',use_container_width=True, type='secondary'):

            # 检查结束列是否为空，如果为空则提示用户
            if not end_col:
                st.error('结束列不能为空！')

            # 检查拆分依据列是否为空，如果为空则提示用户
            if not group_col:
                st.error('拆分分组依据列不能为空！')

            # 如果结束列和拆分依据列任意为空时，则不进行拆分
            if not end_col or not group_col:
                st.stop()

            # 区分文件类型，如果是csv文件，则读取csv
            df = read_table_file(excel_path)

            # 判断df中，有哪几个列中,只有整数，且最长的数字超过10位
            long_digit_cols = convert_long_digit_cols_to_str(df)

            # 定义进度条
            progress_text = "✈️拆分中，请稍等..."
            my_bar = st.progress(0)
            my_bar.text(progress_text)

            # 获取分组的总数以计算进度
            total_groups = len(df[group_col].unique())
            current_group_number = 0

            # 创建一个BytesIO对象来存储压缩包
            zip_buffer = io.BytesIO()

            # 创建一个ZipFile对象，用于添加Excel文件
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                for group, data in df.groupby(group_col):
                    # 生成安全的组名
                    safe_group_name = str(group).replace(':', '-').replace('/', '-')
                    excel_buffer = io.BytesIO()

                    # 保存DataFrame到excel buffer中
                    data.iloc[:, :col_names.index(end_col) + 1].to_excel(excel_buffer, index=False)

                    # 将buffer的内容添加到zip文件中
                    zip_file.writestr(f'{safe_group_name}.xlsx', excel_buffer.getvalue())

                    # 更新当前处理的组号
                    current_group_number += 1

                    # 更新进度条
                    progress = int(current_group_number / total_groups * 100)
                    my_bar.progress(progress, text=progress_text)

            # 设置一个短日期和时间的字符串
            short_date_time = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")

            # 使用Streamlit的download button提供下载
            st.download_button(
                label="下载拆分结果",
                data=zip_buffer,
                file_name=f"表格拆分结果-{short_date_time}.zip",
                mime="application/zip",
                use_container_width=True,
                type='primary'
            )

            # 重置buffer的位置到开始
            zip_buffer.seek(0)

            # 完成后移除进度条和文本
            my_bar.empty()
            st.success('🎉拆分完成！')

            # 清除缓存
            st.cache_resource.clear()

            # 提示用户有那几列被转为了字符串类型
            if long_digit_cols:
                st.info(f'⚠️以下列被转为了字符串类型：{long_digit_cols}')

            st.balloons()



if __name__ == "__main__":
    main()