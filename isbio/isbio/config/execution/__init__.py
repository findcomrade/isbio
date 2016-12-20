from utilz import magic_const, MagicAutoConstEnum


# Static object describing available Executions backends
class ConfigExecList(MagicAutoConstEnum):
	@magic_const
	def Docker(): pass
	
	@magic_const
	def SGE(): pass
	
config_list = ConfigExecList()
