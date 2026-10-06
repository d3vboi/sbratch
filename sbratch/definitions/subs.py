from ..registry import category, define, text, sub

category("subs", "Subroutines", "#3D7BD9", 15)

define("sub_def", "subs", "hat", "define subroutine {name}",
       specs={"name": text("MySub")},
       code=lambda ctx: ["Sub " + ctx.gen.sub_def_name(ctx)],
       tooltip="Sub ... EndSub. Put the blocks the subroutine should run underneath.")

define("sub_call", "subs", "statement", "call subroutine {name}",
       specs={"name": sub()},
       code=lambda ctx: [ctx.gen.use_sub(str(ctx.node.get("fields", {}).get("name", "")), ctx) + "()"],
       tooltip="Runs a subroutine you defined")
