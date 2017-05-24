#!/usr/bin/env python3

from registry.app import registry


registry.run(debug=True, host='0.0.0.0', port=8421)
