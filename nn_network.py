

from google.colab import drive
drive.mount('/content/drive')
path = '/content/drive/My Drive/DL Assignment/Assignment2/'

import pickle
import numpy as np
from numpy import asarray
import pandas as pd
from sklearn.metrics import confusion_matrix

with open(path+'train_set.pkl', 'rb') as f:
    train = pickle.load(f)

with open(path + 'val_set.pkl', 'rb') as f:
    val = pickle.load(f)

"""Processing Input"""

def create_one_hot_encoding(labels_list):
  final_labels_list=[]
  for single_category in labels_list:
    single_list = [0]*10
    single_list[single_category] = 1.0
    #print(single_list)
    final_labels_list.append(single_list)
    
  return final_labels_list

  

def process_input(data):
  features_list = []
  labels_list = []
  for index,row in data.iterrows():
    image = row['Image']
    label = row['Labels']
    pixels_arr = asarray(image)
    d = pixels_arr.flatten()
    features_list.append(d)
    labels_list.append(label)
  pixels_df = pd.DataFrame(list(map(np.ravel, features_list)))
  pixels_df = (pixels_df/255.0).astype('float32')
  final_labels_list=create_one_hot_encoding(labels_list)
  labels_df = pd.DataFrame(final_labels_list)
  return pixels_df, labels_df

X_train,Y_train = process_input(train)
X_test,Y_test = process_input(val)

"""### **Class Definition**"""

class MLPClassifier():
  def __init__(self,layers,num_epochs, dropouts,learning_rate=1e-5,activation_function='relu',optimizer='gradient_descent',weight_init='random',
               regularization='l2',batch_size=64, kwargs = None):
    self.layers = layers
    self.learning_rate = learning_rate
    self.activation_function = activation_function
    self.optimizer = optimizer
    self.weight_init = weight_init
    self.regularization = regularization
    self.batch_size = batch_size
    self.num_epochs = num_epochs
    self.weightMatrix = []
    self.bias_matrix = []
    self.delta_w = []
    self.delta_bias = []
    self.all_weights=[]
    self.all_biases = []
    if kwargs:
      if optimizer == "gradient_descent_momentum" or optimizer == "Nestrov_Accelerated_Gradient":
        self.beta = kwargs['beta']
      if optimizer == "AdaGrad":
        self.epsilon = kwargs['epsilon']
      if optimizer == "RMSProp":
        self.gamma = kwargs['gamma']
        self.epsilon = kwargs['epsilon']
        self.v = [0]* (len(self.layers)-1)
        self.v_bias = [0]* (len(self.layers)-1)
      if optimizer == "Adam":
        self.gamma = kwargs['gamma']
        self.epsilon = kwargs['epsilon']
        self.beta = kwargs['beta']
        self.v = [0]* (len(self.layers)-1)
        self.v_bias = [0]* (len(self.layers)-1)


  def get_params(self):
    return self.weightMatrix

  def sigmoid(self, X):
    s=1/(1+np.exp(-X))
    ds=s*(1-s)  
    return s,ds

  def Softmax(self, X):
      # Numerically stable with large exponentials
      #exps = np.exp(x - x.max())
      #return exps / np.sum(exps, axis=0)
      x=X
      if len(x.shape) > 1:
          tmp = np.max(x, axis = 1)
          x -= tmp.reshape((x.shape[0], 1))
          x = np.exp(x)
          tmp = np.sum(x, axis = 1)
          x /= tmp.reshape((x.shape[0], 1))
      else:
          tmp = np.max(x)
          x -= tmp
          x = np.exp(x)
          tmp = np.sum(x)
          x /= tmp


      return x

  def tanh(self,x):
    t=(np.exp(x)-np.exp(-x))/(np.exp(x)+np.exp(-x))
    dt=1-t**2
    return t,dt

  def relu(self,x):
    #A = np.maximum(-1,x) 
    #dA = (Z>0)*np.ones(Z.shape)
    A = x * (x > 0)
    dA = 1 * (x > 0)
    return A,dA

  def forward_pass(self, X,weights,biases):
    y_output =[X]
    
    z_output =[None]
    layer_number = 0
    # print(len(y_output[layer_number]))
    # print(len(y_output[layer_number][0]))
    # print(len(weights[layer_number]))
    # print(len(weights[layer_number][0]))
    for num in range(0,len(self.layers)-2):
 
      net_output_hidden = np.dot(y_output[layer_number],np.transpose(weights[layer_number])) + np.transpose(biases[layer_number])
      
      z_output.append(net_output_hidden)

      if self.activation_function == "sigmoid":
        y_output_hidden, derivative_value = self.sigmoid(net_output_hidden)
      elif self.activation_function == "relu":
        y_output_hidden, derivative_value = self.relu(net_output_hidden)
      elif self.activation_function == "tanh":
        y_output_hidden, derivative_value = self.tanh(net_output_hidden)

      y_output.append(y_output_hidden)
      layer_number = layer_number +1
    net_output_last_layer = np.dot(y_output[layer_number],np.transpose(weights[layer_number])) + np.transpose(biases[layer_number])
    z_output.append(net_output_last_layer)
    y_output_last_layer = self.Softmax(net_output_last_layer)
    y_output.append(y_output_last_layer)
    return z_output, y_output

  def calculate_loss(self, desired,actual):
    
    loss_value = np.sum(-desired * np.log(actual+1e-8),axis=1)
    list_of_loss_val = loss_value.to_list()
 
    total_loss_value = sum(list_of_loss_val)/len(list_of_loss_val)
    
    return total_loss_value

  def calc_gradient(self,desired,actual,y_output,z_output,weights):
    len_size = len(self.layers)-1
    gradients=[0]*(len(self.layers)-1)
    gradients_bias = [0]*(len(self.layers)-1)
    desired = desired.values.tolist()
    error = actual-desired
    gradient_W2 =  np.transpose(np.dot(np.transpose(y_output[len_size-1]), (actual-desired)))
    gradients[-1] = gradient_W2/self.batch_size
    bias_gradient = np.sum(error,axis=0)
   
   
    gradients_bias[-1] = bias_gradient/self.batch_size
    for k in range(len(self.layers)-2,0,-1):
      error = np.dot(np.transpose(weights[k]),np.transpose(error))
      error = np.transpose(error)
      if self.activation_function == "sigmoid":
        s,ds = self.sigmoid(z_output[k])
      elif self.activation_function == "relu":
        s,ds = self.relu(z_output[k])
      elif self.activation_function == "tanh":
        s,ds = self.tanh(z_output[k])
      error = error * ds
      gradient_W1 = np.transpose(np.dot(np.transpose(y_output[k-1]), error)) 
      gradients[k-1] = gradient_W1/self.batch_size

      bias_gradient_1 =  np.sum(error,axis=0)
      gradients_bias[k-1] = bias_gradient_1/self.batch_size
    return gradients,gradients_bias

  def back_propagation(self, gradients,gradients_bias, X,Y):
    
    if self.optimizer == 'gradient_descent':
      
      for i in range(0,len(self.weightMatrix)):
        a=self.learning_rate*gradients_bias[i]
        self.weightMatrix[i] = np.subtract(self.weightMatrix[i],(self.learning_rate*gradients[i]))
        self.bias_matrix[i] = np.subtract(self.bias_matrix[i], (a[i]))
     
      
    elif self.optimizer == 'gradient_descent_momentum':
      
      for i in range(0,len(self.weightMatrix)):
        self.delta_w[i] = self.beta*self.delta_w[i]-self.learning_rate*gradients[i]
        self.weightMatrix[i] = np.add(self.weightMatrix[i],self.delta_w[i])

        self.delta_bias[i] = self.beta*self.delta_bias[i]-self.learning_rate*gradients_bias[i]
        self.bias_matrix[i] = np.add(self.bias_matrix[i][0],self.delta_bias[i])

    elif self.optimizer == 'Nestrov_Accelerated_Gradient':
    
      weights =[0]*(len(self.layers)-1)
      biases = [0]*(len(self.layers)-1)
      for i in range(0,len(self.weightMatrix)):
        weights[i] = self.weightMatrix[i]+self.beta*self.delta_w[i]
        biases[i] = self.bias_matrix[i]+self.beta*self.delta_bias[i]

      
      z_output, y_output = self.forward_pass(X,weights,biases)
      gradients, bias_gradients_1 = self.calc_gradient(Y,y_output[-1],y_output,z_output,weights)
      for i in range(0,len(self.weightMatrix)):
        self.delta_w[i] = self.beta*self.delta_w[i]-self.learning_rate*gradients[i]
        self.weightMatrix[i] = np.add(self.weightMatrix[i],self.delta_w[i])

        self.delta_bias[i] = self.beta*self.delta_bias[i]-self.learning_rate*bias_gradients_1[i]
        self.bias_matrix[i] = np.add(self.bias_matrix[i][0],self.delta_bias[i])

    elif self.optimizer == 'AdaGrad':
      
      for i in range(0,len(self.weightMatrix)):
        self.delta_w[i] = self.delta_w[i] + gradients[i]**2
        lr = self.learning_rate/np.sqrt(self.delta_w[i]+self.epsilon)
        self.weightMatrix[i] = np.subtract(self.weightMatrix[i],(lr*gradients[i]))
        

        self.delta_bias[i] = self.delta_bias[i] + gradients_bias[i]**2
        lr_bias = self.learning_rate/np.sqrt(self.delta_bias[i]+self.epsilon)
        a = lr_bias*gradients_bias[i]
        
        self.bias_matrix[i] = np.subtract(self.bias_matrix[i][0],(lr_bias*gradients_bias[i]))

    elif self.optimizer == 'RMSProp':
      
      for i in range(0,len(self.weightMatrix)):
        self.delta_w[i] = self.gamma*self.delta_w[i] + (1-self.gamma)*gradients[i]**2
        lr = self.learning_rate/np.sqrt(self.delta_w[i]+self.epsilon)
        self.weightMatrix[i] = np.subtract(self.weightMatrix[i][0],(lr*gradients[i]))
        
        self.delta_bias[i] = self.gamma*self.delta_bias[i] + (1-self.gamma)*gradients_bias[i]**2
        lr_grad = self.learning_rate/np.sqrt(self.delta_bias[i]+self.epsilon)
        self.bias_matrix[i] = np.subtract(self.bias_matrix[i][0],(lr_grad*gradients_bias[i]))

    elif self.optimizer == 'Adam':
       for i in range(0,len(self.weightMatrix)):
        self.delta_w[i] = self.beta*self.delta_w[i]+ self.learning_rate*gradients[i]
        self.v[i] = self.gamma*self.v[i] + (1-self.gamma)*gradients[i]**2
        lr = self.learning_rate/(np.sqrt(self.v[i]+self.epsilon))
        self.weightMatrix[i] = np.subtract(self.weightMatrix[i],(lr*self.delta_w[i]))
        
        self.delta_bias[i] = self.beta*self.delta_bias[i]+ (1-self.beta)*gradients_bias[i]
        self.v_bias[i] = self.gamma*self.v_bias[i] + (1-self.gamma)*gradients_bias[i]**2
        lr_bias = self.learning_rate/np.sqrt(self.v_bias[i]+self.epsilon)
        self.bias_matrix[i] = np.subtract(self.bias_matrix[i][0],(lr_bias*self.delta_bias[i]))


  def set_Weights(self):
    num_layers = len(self.layers)
    layers_neurons = self.layers

    if self.weight_init == "random":
      for i in range(1,num_layers):
        self.weightMatrix.append(np.random.randn(layers_neurons[i],layers_neurons[i-1]))
        self.bias_matrix.append(np.random.randn(layers_neurons[i]))
    if self.optimizer !='gradient_descent':
      self.delta_w = [0]*(len(self.layers)-1)
      self.delta_bias = [0]*(len(self.layers)-1)


  def plot_learning_curves(self,X_train,Y_train,X_test,Y_test):
    list_of_loss_values_testing=[]
    list_of_loss_values_training=[]
    for i in range(0,self.num_epochs):
      
      z_output,y_output =self.forward_pass(X_train,self.all_weights[i],self.all_biases[i])
      loss_value = self.calculate_loss(Y_train,y_output[-1])
      list_of_loss_values_training.append(loss_value)

      z_output,y_output =self.forward_pass(X_test,self.all_weights[i],self.all_biases[i])
      loss_value = self.calculate_loss(Y_test,y_output[-1])
      list_of_loss_values_testing.append(loss_value)
    
    import matplotlib.pyplot as plt
    epochs_list = list(range(1, self.num_epochs+1)) 
    plt.plot(epochs_list, list_of_loss_values_training,color='green', linewidth = 1,label="Training Loss")
    plt.plot(epochs_list, list_of_loss_values_testing,color='orange', linewidth = 1,label="Val Loss")
    plt.xlabel('Number of epochs')
    plt.ylabel('Loss')
    plt.title('Learning curve - Training Loss and Validation Loss')
    plt.legend(loc="lower right")
    plt.show()
    

  def fit(self, X,Y):
    self.set_Weights()
    list_of_loss_values_training=[]
    loss_vs_epochs=[]
    
    for i in range(0,self.num_epochs):
      
      print("Epoch : ",i+1)
      begin = 0
      j=0
      end = begin + self.batch_size
      num_batch=-1
      while begin < end:
      
        num_batch=num_batch+1
      
        X_train_features = X[begin:end]
        Y_train_features = Y[begin:end]
        j=j+1
        begin = j * self.batch_size
        end = min(begin + self.batch_size, X.shape[0])
        
        z_output, y_output = self.forward_pass(X_train_features,self.weightMatrix,self.bias_matrix)
        
        #print("Loss custom : ",loss_value)
        #print("Sklearn loss : ", log_loss(Y_train_features,y_output[-1]) )
        
        
        
        gradients,gradients_bias = self.calc_gradient(Y_train_features,y_output[-1],y_output,z_output,self.weightMatrix)
        self.back_propagation(gradients,gradients_bias,X_train_features,Y_train_features)
        loss_value = self.calculate_loss(Y_train_features,y_output[-1])
        if num_batch%50 == 0:
         print("Loss after batch: %d is %f"%(num_batch+1,loss_value))
      local_weight_matrix = self.weightMatrix[:]
      local_bias_matrix = self.bias_matrix[:]
      self.all_weights.append(local_weight_matrix)
      self.all_biases.append(local_bias_matrix)
      print("Training Loss after complete epoch : ", loss_value)

      
      #print("Validation Loss after complete epoch : ", total_epoch_loss)
    
    #self.visualize_results(list_of_loss_values_training,list_of_loss_values_testing)
   
      

  def predict(self, X_test):
    z_output, y_output = self.forward_pass(X_test,self.weightMatrix,self.bias_matrix)
    Y_pred = []

    for j in range(len(y_output[-1])):
      Y_pred.append(np.argmax(y_output[-1][j]))
    
    return Y_pred

  def predict_proba(self,X):
    z_output, y_output = self.forward_pass(X,self.weightMatrix,self.bias_matrix)
    class_probabilities_matrix = []
    for j in range(len(y_output[-1])):
      class_probabilities_matrix.append(y_output[-1][j])
    return class_probabilities_matrix
  
  def score(self, X, Y_test_actual):
    Y_pred =self.predict(X)
    count = 0
    num_of_rows = len(Y_pred)
    for i in range(0, num_of_rows):
        if(Y_pred[i] == Y_test_actual[i]):
            count= count+1
    classification_accuracy = float(count/num_of_rows)*100
    return classification_accuracy
  
  
  
  
  def visualize_results(self, Y_pred,Y_actual,X,Y_series):
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, auc
    from sklearn.metrics import confusion_matrix
    print("Confusion Matrix")
    print(confusion_matrix(Y_actual,Y_pred))
    
    n_classes=10
    from sklearn import metrics
    df = model.predict_proba(X)
    from sklearn.metrics import roc_curve, auc
    from sklearn.metrics import roc_auc_score
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    
    df = np.asarray(df, dtype=np.float32)
    
    fg = Y_series.to_numpy()
    for i in range(10):
        
        fpr[i], tpr[i], _ = roc_curve(fg[:, i], df[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(fg.ravel(), df.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
    plt.figure()
    lw = 2
    colors = ['aqua', 'magenta','black','brown','green','darkorange', 'cornflowerblue','navy','yellow','cyan']
    for i in range(0,10):
      plt.plot(fpr[i], tpr[i], color=colors[i],
              lw=lw, label=' Label %d - ROC curve  (area = %0.2f)' % (i,roc_auc[i]))
      plt.plot([0, 1], [0, 1], color='blue', lw=lw, linestyle='--')
      plt.xlim([0.0, 1.0])
      plt.ylim([0.0, 1.05])
      plt.xlabel('False Positive Rate')
      plt.ylabel('True Positive Rate')
      plt.title('Receiver operating characteristic example')
      plt.legend(loc="lower right")
    plt.show()



Model Variables
"""

num_neurons_input = 784
num_neurons_output = 10

num_training_instances = len(Y_train)
Y_test_actual = []

for index,row in Y_test.iterrows():
  Y_test_actual.append(np.argmax(row.tolist()))
Y_train_actual = []
for index,row in Y_train.iterrows():
  Y_train_actual.append(np.argmax(row.tolist()))
network_arch_list=[num_neurons_input,100,50,num_neurons_output]

"""### **Sigmoid**"""

network_arch_list=[784,100,50,10]
model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,activation_function='sigmoid' ,batch_size=10000,num_epochs=150,dropouts = 0)
model.fit(X_train,Y_train)

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **Tanh**"""

network_arch_list=[784,100,50,10]
model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,activation_function='tanh' ,batch_size=10000,num_epochs=150,dropouts = 0)
model.fit(X_train,Y_train)
import pickle
pickle.dump(model, open(path+'tanh_ques1'+'.sav', 'wb'))
model = pickle.load(open(path+'tanh_ques1'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **Relu**"""

network_arch_list=[784,100,50,10]
model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,activation_function='relu' ,batch_size=10000,num_epochs=150,dropouts = 0)
model.fit(X_train,Y_train)
import pickle
pickle.dump(model, open(path+'relu_ques1'+'.sav', 'wb'))
model = pickle.load(open(path+'relu_ques1'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""# **Question 2**

### **Gradient Descent with Momentum**
"""

gd_nag_kwargs = {'beta':0.9}
adagrad_kwargs = {'epsilon':1e-8}
rmsprop_kwargs = {'gamma':0.9, 'epsilon':1e-8}
adam_kwargs = {'gamma':0.999, 'epsilon':1e-8,'beta':0.9}

#network_arch_list=[784,100,50,10]
# model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,optimizer="gradient_descent_momentum",num_epochs=100,dropouts = 0,kwargs=gd_nag_kwargs)
# model.fit(X_train,Y_train)

# pickle.dump(model, open(path+'gdmomentum_ques2'+'.sav', 'wb'))
model = pickle.load(open(path+'gdmomentum_ques2'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **Nesterov Accelerated gradient**"""

# network_arch_list=[784,100,50,10]
# model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,optimizer="Nestrov_Accelerated_Gradient" ,kwargs=gd_nag_kwargs,num_epochs=100,dropouts = 0)
# model.fit(X_train,Y_train)

# pickle.dump(model, open(path+'nag_ques2'+'.sav', 'wb'))
model = pickle.load(open(path+'nag_ques2'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **AdaGrad**"""

#network_arch_list=[784,100,50,10]
#model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,optimizer="AdaGrad" ,kwargs=adagrad_kwargs,num_epochs=100,dropouts = 0)
#model.fit(X_train,Y_train)

#pickle.dump(model, open(path+'adagrad_ques2'+'.sav', 'wb'))
model = pickle.load(open(path+'adagrad_ques2'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **Adam**"""

network_arch_list=[784,100,50,10]
model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,optimizer="Adam" ,kwargs=adam_kwargs,num_epochs=100,dropouts = 0)
model.fit(X_train,Y_train)

pickle.dump(model, open(path+'adam_ques2'+'.sav', 'wb'))
#model = pickle.load(open(path+'rmsprop_ques2'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""### **RMSProp**"""

network_arch_list=[784,100,50,10]
model = MLPClassifier(layers=network_arch_list,learning_rate=0.001,optimizer="RMSProp" ,kwargs=rmsprop_kwargs,num_epochs=100,dropouts = 0)
model.fit(X_train,Y_train)

pickle.dump(model, open(path+'rms_q2'+'.sav', 'wb'))
#model = pickle.load(open(path+'adam_ques2'+'.sav', 'rb'))

Y_pred = model.predict(X_train)
classification_accuracy =model.score(X_train,Y_train_actual)
print("Training Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_train_actual,X_train,Y_train)

Y_pred = model.predict(X_test)
classification_accuracy =model.score(X_test,Y_test_actual)
print("Testing Accuracy of model:",classification_accuracy)
model.visualize_results(Y_pred,Y_test_actual,X_test,Y_test)

model.plot_learning_curves(X_train,Y_train,X_test,Y_test)

"""# Analysis"""

num_neurons_hid_1 = [100,200,256,512]
num_neurons_hid2 =[50,100,256,512]
#num_neurons_hid3 = [10,20,30,50]
ne = [10,50,100,150]

for i in range(4):
    #network_arch_list=[num_neurons_input, num_neurons_hid_1[i],num_neurons_hid2[i],50,num_neurons_output]
    network_arch_list=[num_neurons_input, 100,num_neurons_hid2[i],num_neurons_output]
    #network_arch_list=[num_neurons_input, num_neurons_hid_1[i],50,num_neurons_output]

    model = MLPClassifier(layers=network_arch_list,learning_rate=0.0001,activation_function='relu',num_epochs=ne[i],dropouts = 0)
    #model = MLPClassifier(layers=network_arch_list,learning_rate=0.0001,activation_function='sigmoid',num_epochs=ne[i],dropouts = 0)
    #model = MLPClassifier(layers=network_arch_list,learning_rate=0.0001,activation_function='tanh',num_epochs=ne[i],dropouts = 0)
    #model = MLPClassifier(layers=network_arch_list,learning_rate=0.0001,activation_function='relu',num_epochs=150,dropouts = 0)
    model.fit(X_train,Y_train)
    
    Y_pred = model.predict(X_test)

    classification_accuracy =model.score(Y_pred,Y_test_actual)
    print("Accuracy of model:",classification_accuracy)
