# murfai_tts
# MurfAI TTS Custom Component for Home Assistant

This custom component integrates MurfAI's Text-to-Speech (TTS) service with Home Assistant, allowing users to convert text into spoken audio. The service supports various languages and styles, offering customizable options such as style model.

## Description

The MurfAI TTS component for Home Assistant makes it possible to use the MurfAI API to generate spoken audio from text. This can be used in automations, assistants, scripts, or any other component that supports TTS within Home Assistant.

## Features

- Text-to-Speech conversion using MurfAI's API
- Using public anonymous TTS
- It is free to use - for now.

## Sample Home Assistant service

```
service: tts.speak
target:
  entity_id: tts.murfai_nova_engine
data:
  cache: true
  media_player_entity_id: media_player.bedroom_speaker
  message: My speech has improved now!
```

## HACS installation ( *preferred!* ) 

1. Go to the sidebar HACS menu 

2. Click on the 3-dot overflow menu in the upper right and select the "Custom Repositories" item.

3. Copy/paste https://github.com/bbcelly/murfai_tts into the "Repository" textbox and select "Integration" for the category entry.

4. Click on "Add" to add the custom repository.

5. You can then click on the "MurfAI TTS Speech Services" repository entry and download it. Restart Home Assistant to apply the component.

6. Add the integration via UI, provide API key and select required model and style. Multiple instances may be configured.

## Manual installation

1. Ensure you have a `custom_components` folder within your Home Assistant configuration directory.

2. Inside the `custom_components` folder, create a new folder named `murfai_tts`.

3. Place the repo files inside `murfai_tts` folder.

4. Restart Home Assistant

5. Add the integration via UI, provide API key and select required model and style. Multiple instances may be configured.
