# /vision — Analyze Images with AI Vision

Invoke the MCP image analysis tool. Use this when you need to extract information from images, screenshots, mockups, or diagrams.

## Usage

```
/vision <url> [prompt]
```

- `<url>` — Remote URL to the image (PNG, JPG, JPEG)
- `[prompt]` — Optional: what to look for (default: comprehensive analysis)

## Examples

```
/vision https://example.com/mockup.png
/vision https://example.com/screenshot.jpg "Extract the hex color codes used"
/vision https://example.com/diagram.png "Describe the architecture shown"
```

## For UI Replication

When replicating a UI from an image:

```
/vision https://example.com/design.png "replicate"
```

This triggers the special replication prompt: "Describe in detail the layout structure, color style, main components, and interactive elements of the website in this image to facilitate subsequent code generation by the model."

## Local Images

For local image files, use the Read tool directly instead:

```
Read: screenshots/mockup.png
```

The Read tool also supports image viewing for local paths.

## When to Use

- Analyzing hosted screenshots or mockups
- Extracting colors, fonts, spacing from designs
- Understanding diagrams or architecture images
- UI/UX replication tasks
- Reading text from images (OCR-ish)

## Tool Invoked

This command invokes: `mcp__4_5v_mcp__analyze_image`

## Execution

When this command is invoked:

1. Parse the URL and optional prompt from arguments
2. If prompt is "replicate", use the specialized replication prompt
3. Call `mcp__4_5v_mcp__analyze_image` with:
   - `imageSource`: the provided URL
   - `prompt`: the provided prompt (or default comprehensive analysis)
4. Return the analysis results
