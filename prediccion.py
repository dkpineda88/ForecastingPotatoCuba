# import tensorflow as tf
# import numpy as np
#
# celsius = np.array([-40, -10, -39, -32],dtype=float)
# farhenhiet = np.array([-30, -20, -29, -30],dtype=float)
#
# capa = tf.keras.layers.Dense(units=1, input_shape=[1])
# modelo = tf.keras.Sequential([capa])
#
# modelo.compiler(optimizer=tf.keras.optimizer.Adam(0.1))
# loss = 'mean_squared_error'
#
# print('Comenzando entrenamiento')
# historial = modelo.fit(celsius, farhenhiet, epochs=1000, verbose=False)
# print('Ya se entreno')
#
# import matplotlib as mtl
# mtl.xlabel('Epoca')
# mtl.ylabel('Magnitud de perdida')
# mtl.plot(historial.history['loss'])
#
# resultado = modelo.predict([100.0])
# print('El resultado es:'+ str(resultado))
#
