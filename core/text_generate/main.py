from core.text_generate.generator import CopyGenerator


def get_copy_generator(category, style, input_data):
    generator = CopyGenerator()
    # 示例数据：电商带货 - 悬念互动型

    result = generator.generate(category, style, input_data)
    print("生成文案：\n", result)
    return result


if __name__ == "__main__":
    input_data = {
        "商品名称": "智能按摩腰带",
        "商品亮点": "恒温热敷+智能调节力度",
        "适用人群": "久坐上班族、腰肌劳损人群",
        "视频时长": "30秒"
    }
    get_copy_generator('ecom', 'suspense', input_data)


