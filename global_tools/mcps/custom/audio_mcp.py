#!/usr/bin/env python3
"""
Audio Processing MCP Server

This MCP server provides audio processing capabilities for audio enhancement applications.
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

class AudioProcessingMCPServer:
    def __init__(self):
        self.tools = {
            "analyze_audio": {
                "name": "analyze_audio",
                "description": "Analyze audio file properties (duration, format, sample rate)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to audio file"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            "convert_audio": {
                "name": "convert_audio",
                "description": "Convert audio file to different format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Path to input audio file"
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output format (mp3, wav, flac, ogg)",
                            "enum": ["mp3", "wav", "flac", "ogg"]
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Optional output file path"
                        }
                    },
                    "required": ["input_file", "output_format"]
                }
            },
            "normalize_audio": {
                "name": "normalize_audio",
                "description": "Normalize audio volume levels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Path to input audio file"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Optional output file path"
                        }
                    },
                    "required": ["input_file"]
                }
            },
            "trim_audio": {
                "name": "trim_audio",
                "description": "Trim audio to specified time range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Path to input audio file"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "Start time in seconds"
                        },
                        "end_time": {
                            "type": "number",
                            "description": "End time in seconds"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Optional output file path"
                        }
                    },
                    "required": ["input_file", "start_time", "end_time"]
                }
            },
            "merge_audio": {
                "name": "merge_audio",
                "description": "Merge multiple audio files",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of audio file paths"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Output file path"
                        }
                    },
                    "required": ["input_files", "output_file"]
                }
            },
            "extract_audio": {
                "name": "extract_audio",
                "description": "Extract segment from audio file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Path to input audio file"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "Start time in seconds"
                        },
                        "duration": {
                            "type": "number",
                            "description": "Duration in seconds"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Output file path"
                        }
                    },
                    "required": ["input_file", "start_time", "duration", "output_file"]
                }
            }
        }

    def list_tools(self):
        return list(self.tools.values())

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": self.list_tools()}
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "analyze_audio":
            return self._analyze_audio(arguments)
        elif tool_name == "convert_audio":
            return self._convert_audio(arguments)
        elif tool_name == "normalize_audio":
            return self._normalize_audio(arguments)
        elif tool_name == "trim_audio":
            return self._trim_audio(arguments)
        elif tool_name == "merge_audio":
            return self._merge_audio(arguments)
        elif tool_name == "extract_audio":
            return self._extract_audio(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _analyze_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        file_path = args["file_path"]
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Use ffprobe for audio analysis if available
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "file_path": file_path,
                    "analysis": data,
                    "file_size": os.path.getsize(file_path),
                    "method": "ffprobe"
                }
        except:
            pass
        
        # Fallback analysis
        file_size = os.path.getsize(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        return {
            "file_path": file_path,
            "format": file_ext,
            "file_size_bytes": file_size,
            "note": "Install ffmpeg/ffprobe for detailed audio analysis"
        }

    def _convert_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        input_file = args["input_file"]
        output_format = args["output_format"]
        output_file = args.get("output_file")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not output_file:
            base = Path(input_file).stem
            output_file = f"{base}_converted.{output_format}"
        
        # Use ffmpeg for conversion
        try:
            cmd = ["ffmpeg", "-i", input_file, "-y", output_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "input_file": input_file,
                    "output_file": output_file,
                    "output_format": output_format,
                    "conversion_successful": True,
                    "output_size": os.path.getsize(output_file)
                }
            else:
                return {
                    "input_file": input_file,
                    "error": "ffmpeg conversion failed",
                    "ffmpeg_output": result.stderr
                }
        except Exception as e:
            return {
                "input_file": input_file,
                "error": f"Conversion failed: {str(e)}",
                "note": "Install ffmpeg for audio conversion"
            }

    def _normalize_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        input_file = args["input_file"]
        output_file = args.get("output_file")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not output_file:
            base = Path(input_file).stem
            ext = Path(input_file).suffix
            output_file = f"{base}_normalized{ext}"
        
        # Use ffmpeg for normalization
        try:
            cmd = [
                "ffmpeg", "-i", input_file,
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-y", output_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "input_file": input_file,
                    "output_file": output_file,
                    "normalization_successful": True,
                    "output_size": os.path.getsize(output_file)
                }
            else:
                return {
                    "input_file": input_file,
                    "error": "Normalization failed",
                    "note": "Using ffmpeg loudnorm filter"
                }
        except:
            return {
                "input_file": input_file,
                "note": "Audio normalization requires ffmpeg with loudnorm filter"
            }

    def _trim_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        input_file = args["input_file"]
        start_time = args["start_time"]
        end_time = args["end_time"]
        output_file = args.get("output_file")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not output_file:
            base = Path(input_file).stem
            ext = Path(input_file).suffix
            output_file = f"{base}_trimmed{ext}"
        
        duration = end_time - start_time
        
        # Use ffmpeg for trimming
        try:
            cmd = [
                "ffmpeg", "-i", input_file,
                "-ss", str(start_time),
                "-t", str(duration),
                "-y", output_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "input_file": input_file,
                    "output_file": output_file,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "trim_successful": True,
                    "output_size": os.path.getsize(output_file)
                }
            else:
                return {
                    "input_file": input_file,
                    "error": "Trimming failed",
                    "ffmpeg_output": result.stderr
                }
        except:
            return {
                "input_file": input_file,
                "note": "Audio trimming requires ffmpeg"
            }

    def _merge_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        input_files = args["input_files"]
        output_file = args["output_file"]
        
        # Check all input files exist
        for f in input_files:
            if not os.path.exists(f):
                raise FileNotFoundError(f"Input file not found: {f}")
        
        # Create file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for input_file in input_files:
                f.write(f"file '{input_file}'\n")
            list_file = f.name
        
        try:
            # Use ffmpeg concat
            cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", list_file, "-y", output_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            os.unlink(list_file)
            
            if result.returncode == 0:
                return {
                    "input_files": input_files,
                    "output_file": output_file,
                    "merge_successful": True,
                    "output_size": os.path.getsize(output_file)
                }
            else:
                return {
                    "input_files": input_files,
                    "error": "Merge failed",
                    "ffmpeg_output": result.stderr
                }
        except Exception as e:
            if os.path.exists(list_file):
                os.unlink(list_file)
            return {
                "input_files": input_files,
                "error": f"Merge failed: {str(e)}",
                "note": "Audio merging requires ffmpeg"
            }

    def _extract_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        input_file = args["input_file"]
        start_time = args["start_time"]
        duration = args["duration"]
        output_file = args["output_file"]
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Use ffmpeg for extraction
        try:
            cmd = [
                "ffmpeg", "-i", input_file,
                "-ss", str(start_time),
                "-t", str(duration),
                "-y", output_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "input_file": input_file,
                    "output_file": output_file,
                    "start_time": start_time,
                    "duration": duration,
                    "extraction_successful": True,
                    "output_size": os.path.getsize(output_file)
                }
            else:
                return {
                    "input_file": input_file,
                    "error": "Extraction failed",
                    "ffmpeg_output": result.stderr
                }
        except:
            return {
                "input_file": input_file,
                "note": "Audio extraction requires ffmpeg"
            }


def main():
    """Main entry point for the MCP server"""
    server = AudioProcessingMCPServer()
    
    # Read requests from stdin, write responses to stdout
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()