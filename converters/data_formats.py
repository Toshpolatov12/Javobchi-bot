import asyncio
import logging
import json
import xmltodict
import yaml

logger = logging.getLogger(__name__)

def _xml_to_json(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        parsed = xmltodict.parse(xml_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=4)
        return output_path
    except Exception as e:
        logger.error(f"Error converting xml to json: {e}")
        raise

async def convert_xml_to_json(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xml_to_json, input_path, output_path)

def _json_to_xml(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        xml_content = xmltodict.unparse(data, pretty=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        return output_path
    except Exception as e:
        logger.error(f"Error converting json to xml: {e}")
        raise

async def convert_json_to_xml(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_json_to_xml, input_path, output_path)

def _yaml_to_json(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return output_path
    except Exception as e:
        logger.error(f"Error converting yaml to json: {e}")
        raise

async def convert_yaml_to_json(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_yaml_to_json, input_path, output_path)

def _json_to_yaml(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return output_path
    except Exception as e:
        logger.error(f"Error converting json to yaml: {e}")
        raise

async def convert_json_to_yaml(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_json_to_yaml, input_path, output_path)

def _yaml_to_xml(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # xmltodict requires a single root. we wrap it if needed.
        if not isinstance(data, dict) or len(data) != 1:
            data = {'root': data}
            
        xml_content = xmltodict.unparse(data, pretty=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        return output_path
    except Exception as e:
        logger.error(f"Error converting yaml to xml: {e}")
        raise

async def convert_yaml_to_xml(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_yaml_to_xml, input_path, output_path)

def _xml_to_yaml(input_path: str, output_path: str) -> str:
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        parsed = xmltodict.parse(xml_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(parsed, f, default_flow_style=False)
        return output_path
    except Exception as e:
        logger.error(f"Error converting xml to yaml: {e}")
        raise

async def convert_xml_to_yaml(input_path: str, output_path: str) -> str:
    return await asyncio.to_thread(_xml_to_yaml, input_path, output_path)

CONVERTERS = {
    ('xml', 'json'): convert_xml_to_json,
    ('json', 'xml'): convert_json_to_xml,
    ('yaml', 'json'): convert_yaml_to_json,
    ('yml', 'json'): convert_yaml_to_json,
    ('json', 'yaml'): convert_json_to_yaml,
    ('json', 'yml'): convert_json_to_yaml,
    ('yaml', 'xml'): convert_yaml_to_xml,
    ('yml', 'xml'): convert_yaml_to_xml,
    ('xml', 'yaml'): convert_xml_to_yaml,
    ('xml', 'yml'): convert_xml_to_yaml,
}
