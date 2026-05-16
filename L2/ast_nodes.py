class IRBuilder:
    def __init__(self):
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def add_instruction(self, op, arg1, arg2, res):
        self.code.append({'op': op, 'arg1': arg1, 'arg2': arg2, 'res': res, 'label': None})

    def add_label(self, label):
        self.code.append({'op': 'LABEL', 'arg1': None, 'arg2': None, 'res': None, 'label': label})

    def format_ir(self, code):
        res = []
        for instr in code:
            if instr['op'] == 'LABEL':
                res.append(f"{instr['label']}:")
            elif instr['op'] == '=':
                res.append(f"    {instr['res']} = {instr['arg1']}")
            elif instr['op'] == 'ifFalse':
                res.append(f"    ifFalse {instr['arg1']} goto {instr['res']}")
            elif instr['op'] == 'goto':
                res.append(f"    goto {instr['arg1']}")
            elif instr['op'] == 'phi':
                args_str = ", ".join(instr['arg1'])
                res.append(f"    {instr['res']} = phi({args_str})")
            else:
                arg2_str = f" {instr['arg2']}" if instr['arg2'] is not None else ""
                res.append(f"    {instr['res']} = {instr['arg1']} {instr['op']}{arg2_str}")
        return "\n".join(res)


def optimize_while_to_for(code):
    transformed = []
    i = 0
    n = len(code)
    while i < n:
        if (i < n - 3 and
                code[i]['op'] == 'LABEL' and
                code[i + 1]['op'] in ('<', '<=', '>', '>=', '==', '!=') and
                code[i + 2]['op'] == 'ifFalse'):

            start_label = code[i]['label']
            cond = code[i + 1]
            if_false = code[i + 2]
            end_label = if_false['res']

            body = []
            j = i + 3
            loop_end_found = False
            while j < n:
                if code[j]['op'] == 'goto' and code[j]['arg1'] == start_label:
                    if j + 1 < n and code[j + 1]['op'] == 'LABEL' and code[j + 1]['label'] == end_label:
                        loop_end_found = True
                        j += 2
                        break
                body.append(code[j])
                j += 1

            if loop_end_found:
                for_init_label = f"FOR_INIT_{start_label}"
                for_cond_label = f"FOR_COND_{start_label}"
                for_step_label = f"FOR_STEP_{start_label}"
                for_end_label = f"FOR_END_{end_label}"

                loop_vars = set()
                for b_instr in body:
                    if b_instr['op'] == '=' and b_instr['res']:
                        loop_vars.add(b_instr['res'])

                step_instrs = []
                body_instrs = []
                for b_instr in body:
                    if b_instr['op'] in ('+', '-') and b_instr['res'] in loop_vars and b_instr['arg1'] == b_instr[
                        'res']:
                        step_instrs.append(b_instr)
                    elif b_instr['op'] == '=' and b_instr['res'] in loop_vars and any(
                            s['res'] == b_instr['arg1'] for s in step_instrs):
                        step_instrs.append(b_instr)
                    else:
                        body_instrs.append(b_instr)

                transformed.append({'op': 'LABEL', 'arg1': None, 'arg2': None, 'res': None, 'label': for_init_label})
                transformed.append({'op': 'LABEL', 'arg1': None, 'arg2': None, 'res': None, 'label': for_cond_label})
                transformed.append(cond)

                new_if_false = if_false.copy()
                new_if_false['res'] = for_end_label
                transformed.append(new_if_false)

                for b_instr in body_instrs:
                    transformed.append(b_instr)

                transformed.append({'op': 'LABEL', 'arg1': None, 'arg2': None, 'res': None, 'label': for_step_label})
                for s_instr in step_instrs:
                    transformed.append(s_instr)

                transformed.append({'op': 'goto', 'arg1': for_cond_label, 'arg2': None, 'res': None, 'label': None})
                transformed.append({'op': 'LABEL', 'arg1': None, 'arg2': None, 'res': None, 'label': for_end_label})
                i = j
                continue
        transformed.append(code[i])
        i += 1
    return transformed


def optimize_increment_to_ssa(code):
    ssa_code = []
    versions = {}

    loop_headers = set()
    loop_vars = set()

    for instr in code:
        if instr['op'] == 'goto' and instr['arg1']:
            loop_headers.add(instr['arg1'])

    for instr in code:
        if instr['op'] in ('=', '+', '-', '*', '/') and instr['res']:
            res = instr['res']
            if isinstance(res, str) and not res.startswith('t') and not res.startswith('L') and not res.startswith(
                    'FOR_'):
                loop_vars.add(res)

    def get_ver(var):
        if isinstance(var, str) and var in loop_vars:
            return f"{var}_{versions.get(var, 0)}"
        return var

    def next_ver(var):
        if isinstance(var, str) and var in loop_vars:
            versions[var] = versions.get(var, 0) + 1
            return f"{var}_{versions[var]}"
        return var

    phi_nodes_to_patch = []

    for instr in code:
        new_instr = instr.copy()

        if new_instr['op'] == 'LABEL':
            ssa_code.append(new_instr)
            if new_instr['label'] in loop_headers:
                for var in sorted(list(loop_vars)):
                    init_ver = f"{var}_{versions.get(var, 0)}"
                    next_v = f"{var}_{versions.get(var, 0) + 1}"
                    versions[var] = versions.get(var, 0) + 1

                    phi_instr = {'op': 'phi', 'arg1': [init_ver, 'PENDING'], 'arg2': None, 'res': next_v, 'label': None}
                    ssa_code.append(phi_instr)
                    phi_nodes_to_patch.append((var, phi_instr))
            continue

        if new_instr['arg1'] is not None:
            new_instr['arg1'] = get_ver(new_instr['arg1'])
        if new_instr['arg2'] is not None:
            new_instr['arg2'] = get_ver(new_instr['arg2'])

        if new_instr['op'] in ('ifFalse', 'goto'):
            ssa_code.append(new_instr)
            continue

        if new_instr['res'] is not None:
            if new_instr['res'] in loop_vars:
                new_instr['res'] = next_ver(new_instr['res'])
            else:
                if isinstance(new_instr['res'], str) and new_instr['res'].startswith('t'):
                    new_instr['res'] = next_ver(new_instr['res'])

        ssa_code.append(new_instr)

    for var, phi_instr in phi_nodes_to_patch:
        phi_instr['arg1'][1] = f"{var}_{versions.get(var, 0)}"

    return ssa_code


class ASTNode:
    def get_tree_str(self, prefix="", is_last=True, name=""):
        return ""

    def get_node_label(self):
        return self.__class__.__name__

    def get_children(self):
        return []

    def generate_tac(self, builder):
        pass


class VarNode(ASTNode):
    def __init__(self, name, line, column):
        self.name = name
        self.line = line
        self.column = column

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        return f"{prefix}{marker}{name}VarNode: {self.name}\n"

    def get_node_label(self):
        return f"VarNode\nname: {self.name}"

    def generate_tac(self, builder):
        return self.name


class NumberNode(ASTNode):
    def __init__(self, value, line, column):
        self.value = value
        self.line = line
        self.column = column

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        return f"{prefix}{marker}{name}NumberNode: {self.value}\n"

    def get_node_label(self):
        return f"NumberNode\nval: {self.value}"

    def generate_tac(self, builder):
        return self.value


class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        res = f"{prefix}{marker}{name}BinOpNode ({self.op})\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        if self.left: res += self.left.get_tree_str(child_prefix, False, "left: ")
        if self.right: res += self.right.get_tree_str(child_prefix, True, "right: ")
        return res

    def get_node_label(self):
        return f"BinOpNode\nop: {self.op}"

    def get_children(self):
        return [("left", self.left), ("right", self.right)]

    def generate_tac(self, builder):
        left_val = self.left.generate_tac(builder)
        right_val = self.right.generate_tac(builder)
        res = builder.new_temp()
        builder.add_instruction(self.op, left_val, right_val, res)
        return res


class UnaryOpNode(ASTNode):
    def __init__(self, operand, op):
        self.operand = operand
        self.op = op

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        res = f"{prefix}{marker}{name}UnaryOpNode ({self.op})\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        if self.operand: res += self.operand.get_tree_str(child_prefix, True, "operand: ")
        return res

    def get_node_label(self):
        return f"UnaryOpNode\nop: {self.op}"

    def get_children(self):
        return [("operand", self.operand)]

    def generate_tac(self, builder):
        operand_val = self.operand.generate_tac(builder)
        if self.op in ('++', '--'):
            math_op = '+' if self.op == '++' else '-'
            t = builder.new_temp()
            builder.add_instruction(math_op, operand_val, 1, t)
            builder.add_instruction('=', t, None, operand_val)
            return operand_val
        else:
            t = builder.new_temp()
            builder.add_instruction(self.op, operand_val, None, t)
            return t


class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        res = f"{prefix}{marker}{name}BlockNode\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, stmt in enumerate(self.statements):
            res += stmt.get_tree_str(child_prefix, i == len(self.statements) - 1, "stmt: ")
        return res

    def get_children(self):
        return [("stmt", s) for s in self.statements]

    def generate_tac(self, builder):
        for stmt in self.statements:
            stmt.generate_tac(builder)


class WhileNode(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def get_tree_str(self, prefix="", is_last=True, name=""):
        marker = "└── " if is_last else "├── "
        res = f"{prefix}{marker}{name}WhileNode\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        if self.condition: res += self.condition.get_tree_str(child_prefix, False, "cond: ")
        if self.body: res += self.body.get_tree_str(child_prefix, True, "body: ")
        return res

    def get_children(self):
        return [("condition", self.condition), ("body", self.body)]

    def generate_tac(self, builder):
        start_lbl = builder.new_label()
        end_lbl = builder.new_label()

        builder.add_label(start_lbl)
        cond_val = self.condition.generate_tac(builder)
        builder.add_instruction('ifFalse', cond_val, None, end_lbl)

        self.body.generate_tac(builder)
        builder.add_instruction('goto', start_lbl, None, None)

        builder.add_label(end_lbl)