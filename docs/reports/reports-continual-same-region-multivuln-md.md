# Same-region multi-vulnerability benchmark

- Oracle independent triggers: `{'PV-DELIM-BACKDOOR': True, 'PV-SR-ENCODING': True, 'PV-SR-RAREFRAG': True}`
- Region after A priority=0.752 saturated=False
- Guided discovery unique: ['PV-DELIM-BACKDOOR', 'PV-SR-ENCODING', 'PV-SR-RAREFRAG']
- Stateless cumulative unique (3×24): 3
- Continual cumulative unique (3×24): 3
- Continual improved vs stateless: **False**

See `same_region_multivuln.json` for full curves.

- Continual runs_to_all_sr=1, stateless=3, faster=True
