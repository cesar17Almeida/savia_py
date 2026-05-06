"""
Inferencia ML on-device.

Contenido previsto:
  - load_model(path)  : carga TFLite (preferir int8 cuantizado)
  - run_inference()   : entrada → predicción → resultado a storage
  - InferenceProcess  : wrapper sobre multiprocessing.Process

Corre en un proceso aparte (no thread): la inferencia es CPU-bound y
en un hilo se come el GIL, matando la cadencia del resto.

Disparado por lora.downlink_handler ("orden desde cloud") o por
schedule local definido en config.
"""
