import registry.Registry 

def test_reg_chan():
    chan_services=Registry.query(source='chanmaster',service_type='cone')
    assert "ivo://nasa.heasarc/chanmaster" in chan_services[0]['ivoid']
