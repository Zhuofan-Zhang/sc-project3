if __name__ == "__main__":
    import re

    # 定义要匹配的字符串
    string_to_match = "/house1/room1/device1/light"
    command = "command:off"

    # 定义正则表达式
    # 这个例子中的正则表达式用于匹配美国风格的电话号码
    # pattern = re.compile(r'command')

    # 使用search方法查找第一个匹配项
    # match = pattern.search(command)
    command_array = []

    # 如果匹配成功，打印匹配的字符串
    if re.compile(r'command').search(command):
        command_array = string_to_match.split('/')[-1]

        print(command_array, command.split(':')[-1])
    else:
        print("No match found.")
