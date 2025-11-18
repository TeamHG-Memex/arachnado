# Arachnado Examples

This directory contains example code for using Arachnado features.

## Custom Spiders

The `custom_spiders` directory contains example custom spiders that demonstrate
how to create and use custom Scrapy spiders with Arachnado.

### Using the Example Spiders

1. Add this examples directory to your Python path:
   ```bash
   export PYTHONPATH=/path/to/arachnado/examples:$PYTHONPATH
   ```

2. Configure Arachnado to load the example spiders by creating or editing
   your config file (e.g., `~/.arachnado.conf`):
   ```ini
   [arachnado.scrapy]
   spider_packages = custom_spiders
   ```

3. Start Arachnado:
   ```bash
   arachnado --config ~/.arachnado.conf
   ```

4. In the Arachnado web interface, start a crawl using one of these URLs:
   - `spider://example` - Full-featured example spider with custom parsing
   - `spider://simple` - Simple spider that just extracts titles

### Example Spiders Included

- **example**: Demonstrates a full-featured custom spider that:
  - Inherits from `ArachnadoSpider`
  - Accepts custom arguments (e.g., `max_pages`)
  - Extracts multiple data points (titles, headings, links)
  - Follows links within the same domain
  
- **simple**: A minimal example showing basic spider functionality

### Creating Your Own Spiders

See the [Custom Spiders documentation](../docs/custom-spiders.rst) for detailed
instructions on creating your own custom spiders.

Key points:
- Your spider should have a `name` attribute
- It will receive a `domain` parameter from Arachnado
- Inherit from `ArachnadoSpider` for better integration
- Configure `spider_packages` to tell Arachnado where to find your spiders
- Use `spider://yourspidername` to trigger your custom spider
