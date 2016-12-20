from utilz import magic_const, MagicAutoConstEnum


# Static object describing available Auth Backends
class ConfigAuthMethodsList(MagicAutoConstEnum):
	@magic_const
	def CAS_NG(): pass
	
	@magic_const
	def AUTH0(): pass

config_list = ConfigAuthMethodsList()
