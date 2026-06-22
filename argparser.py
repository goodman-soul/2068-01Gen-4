import sys
from typing import Any, Callable, Dict, List, Optional, Tuple


class ArgumentError(Exception):
    pass


class Argument:
    def __init__(
        self,
        name: str,
        short: Optional[str] = None,
        long: Optional[str] = None,
        required: bool = False,
        default: Any = None,
        help: str = "",
        action: str = "store",
        type: Callable[[str], Any] = str,
        metavar: Optional[str] = None,
    ):
        self.name = name
        self.short = short
        self.long = long
        self.required = required
        self.default = default
        self.help = help
        self.action = action
        self.type = type
        self.metavar = metavar or name.upper()

    def match(self, token: str) -> bool:
        if self.short and token == f"-{self.short}":
            return True
        if self.long and token == f"--{self.long}":
            return True
        if self.long and token.startswith(f"--{self.long}="):
            return True
        return False

    def takes_value(self) -> bool:
        return self.action == "store"


class ArgParser:
    def __init__(self, prog: str = "", description: str = ""):
        self.prog = prog or sys.argv[0]
        self.description = description
        self._args: List[Argument] = []
        self._positionals: List[Argument] = []

    def add_argument(
        self,
        name: str,
        short: Optional[str] = None,
        long: Optional[str] = None,
        required: bool = False,
        default: Any = None,
        help: str = "",
        action: str = "store",
        type: Callable[[str], Any] = str,
        metavar: Optional[str] = None,
    ):
        arg = Argument(
            name=name,
            short=short,
            long=long,
            required=required,
            default=default,
            help=help,
            action=action,
            type=type,
            metavar=metavar,
        )
        if short or long:
            self._args.append(arg)
        else:
            self._positionals.append(arg)

    def parse_args(self, argv: Optional[List[str]] = None) -> Dict[str, Any]:
        if argv is None:
            argv = sys.argv[1:]

        result: Dict[str, Any] = {}
        for arg in self._args:
            if arg.action == "store_true":
                result[arg.name] = False
            elif arg.action == "store_false":
                result[arg.name] = True
            else:
                result[arg.name] = arg.default

        positional_idx = 0
        i = 0
        while i < len(argv):
            token = argv[i]

            if token == "-h" or token == "--help":
                self.print_help()
                sys.exit(0)

            if token.startswith("--") and "=" in token:
                name_part, value_part = token.split("=", 1)
                arg = self._find_arg(name_part)
                if not arg:
                    raise ArgumentError(f"未知选项: {name_part}")
                if not arg.takes_value():
                    raise ArgumentError(f"选项 {token} 不需要参数")
                result[arg.name] = self._convert_type(arg, value_part)
                i += 1
                continue

            if token.startswith("-") and len(token) > 2 and not token.startswith("--"):
                j = 1
                while j < len(token):
                    opt = f"-{token[j]}"
                    arg = self._find_arg(opt)
                    if not arg:
                        raise ArgumentError(f"未知选项: {opt}")
                    if arg.takes_value():
                        if j + 1 < len(token):
                            value = token[j + 1:]
                            result[arg.name] = self._convert_type(arg, value)
                            break
                        else:
                            if i + 1 >= len(argv):
                                raise ArgumentError(f"选项 -{arg.short} 需要参数")
                            result[arg.name] = self._convert_type(arg, argv[i + 1])
                            i += 1
                            break
                    else:
                        if arg.action == "store_true":
                            result[arg.name] = True
                        elif arg.action == "store_false":
                            result[arg.name] = False
                    j += 1
                i += 1
                continue

            arg = self._find_arg(token)
            if arg:
                if arg.action == "store_true":
                    result[arg.name] = True
                elif arg.action == "store_false":
                    result[arg.name] = False
                elif arg.takes_value():
                        if i + 1 >= len(argv):
                            raise ArgumentError(f"选项 {token} 需要参数")
                        result[arg.name] = self._convert_type(arg, argv[i + 1])
                        i += 1
                i += 1
                continue

            if not token.startswith("-"):
                if positional_idx < len(self._positionals):
                    pos_arg = self._positionals[positional_idx]
                    result[pos_arg.name] = self._convert_type(pos_arg, token)
                    positional_idx += 1
                    i += 1
                    continue
                else:
                    raise ArgumentError(f"意外的位置参数: {token}")
            else:
                raise ArgumentError(f"未知选项: {token}")

        for arg in self._args:
            if arg.required and result.get(arg.name) is None:
                raise ArgumentError(f"缺少必需选项: {'/'.join(filter(None, [f'-{arg.short}' if arg.short else '', f'--{arg.long}' if arg.long else '']))}")

        while positional_idx < len(self._positionals):
            pos_arg = self._positionals[positional_idx]
            if pos_arg.required:
                raise ArgumentError(f"缺少必需位置参数: {pos_arg.name}")
            result[pos_arg.name] = pos_arg.default
            positional_idx += 1

        return result

    def _find_arg(self, token: str) -> Optional[Argument]:
        for arg in self._args:
            if arg.match(token):
                return arg
        return None

    def _convert_type(self, arg: Argument, value: str) -> Any:
        try:
            return arg.type(value)
        except ValueError as e:
            raise ArgumentError(f"参数 '{value}' 类型错误: {e}")

    def print_help(self):
        lines = []
        if self.description:
            lines.append(self.description)
            lines.append("")

        usage = f"用法: {self.prog}"
        if self._args:
            usage += " [选项]"
        for pos in self._positionals:
            usage += f" {pos.metavar}"
        lines.append(usage)
        lines.append("")

        if self._positionals:
            lines.append("位置参数:")
            for pos in self._positionals:
                lines.append(f"  {pos.metavar:<12} {pos.help}")
            lines.append("")

        if self._args:
            lines.append("选项:")
            lines.append(f"  -h, --help{'':<10} 显示帮助信息并退出")
            for arg in self._args:
                parts = []
                if arg.short:
                    parts.append(f"-{arg.short}")
                if arg.long:
                    parts.append(f"--{arg.long}")
                flag_str = ", ".join(parts)
                if arg.takes_value():
                    flag_str += f" {arg.metavar}"
                help_str = arg.help
                if arg.default is not None and arg.action == "store":
                    help_str += f" (默认: {arg.default})"
                lines.append(f"  {flag_str:<20} {help_str}")

        print("\n".join(lines))

    def error(self, message: str):
        print(f"{self.prog}: 错误: {message}", file=sys.stderr)
        print(f"使用 '{self.prog} --help' 查看更多信息。", file=sys.stderr)
        sys.exit(1)
