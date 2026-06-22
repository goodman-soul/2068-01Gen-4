import sys
from argparser import ArgParser, ArgumentError


def main():
    parser = ArgParser(
        prog="file-processor",
        description="文件处理工具 - 读取输入文件并输出到指定位置",
    )

    parser.add_argument(
        name="input_file",
        short="i",
        long="input",
        required=True,
        help="要处理的输入文件路径",
        metavar="FILE",
    )

    parser.add_argument(
        name="output_file",
        short="o",
        long="output",
        default="output.txt",
        help="输出文件路径",
        metavar="FILE",
    )

    parser.add_argument(
        name="verbose",
        short="v",
        long="verbose",
        action="store_true",
        help="显示详细处理信息",
    )

    try:
        args = parser.parse_args()
    except ArgumentError as e:
        parser.error(str(e))

    print(f"输入文件: {args['input_file']}")
    print(f"输出文件: {args['output_file']}")
    print(f"详细模式: {'开启' if args['verbose'] else '关闭'}")

    if args["verbose"]:
        print(f"\n[verbose] 开始处理文件: {args['input_file']}")
        print(f"[verbose] 输出将写入: {args['output_file']}")
        print("[verbose] 处理完成!")


if __name__ == "__main__":
    main()
