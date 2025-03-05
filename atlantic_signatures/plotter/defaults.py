"""

"""

from atlantic_signatures.plotter.config_loader import ureg



REQUIRED_CONFIG_SECTIONS = (
    'Field Properties',
    'Current Properties',
    'Goal Properties',
    'Boundary Conditions',
    'Create Properties'
    )

# (section, option): (dtype string, default)
CONFIG_OPTIONS = {
    ('Field Properties', 'a_inc'): ('<float>', None, None),
    ('Field Properties', 'b_inc'): ('<float>', None, None),
    ('Field Properties', 'c_inc'): ('<float>', None, None),
    ('Field Properties', 'a_int'): ('<float>', None, None),
    ('Field Properties', 'b_int'): ('<float>', None, None),
    ('Field Properties', 'c_int'): ('<float>', None, None),
    ('Field Properties', 'beta_0'): ('<quantity>', [0.0, 0.0, 0.0] * ureg.meter, 'meter'),
    ('Field Properties', 'gamma_0'): ('<quantity>', [0.0, 0.0, 0.0] * ureg.meter, 'meter'),
    ('Field Properties', 'eta'): ('<float>', None, None),
    ('Field Properties', 'theta_int'): ('<quantity>', 10 * ureg.degree, 'degree'),
    ('Field Properties', 'lambda'): ('<quantity>', 5 * ureg.degree, 'degree'),
    ('Current Properties', 'v_theta'): ('<quantity>', None, 'm/s'),
    ('Current Properties', 'v_radial'): ('<quantity>', None, 'm/s'),
    ('Current Properties', 'current_source_position'): ('<quantity>', [0.0, 0.0] * ureg.meter, 'meter'),
    ('Current Properties', 'theta_fluid'): ('<quantity>', 5 * ureg.degree, 'degree'),
    ('Current Properties', 's_x'): ('<float>', 2.0, None),
    ('Current Properties', 's_y'): ('<float>', 1.0, None),
    ('Boundary Conditions', 'x_min'): ('<quantity>', -2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'x_max'): ('<quantity>', 2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'y_min'): ('<quantity>', -2.7432 * ureg.meter, 'meter'),
    ('Boundary Conditions', 'y_max'): ('<quantity>', 2.7432 * ureg.meter, 'meter'),
    ('Create Properties', 'linear_velocity'): ('<quantity>', 0.1 * ureg.meter_per_second, 'mm/s'),
    ('Create Properties', 'r_multi'): ('<quantity>', 0.1 * ureg.meter, 'meter'),
    ('Create Properties', 'r_goal'): ('<quantity>', 0.5 * ureg.meter, 'meter'),
    }
