# -*- coding: utf-8 -*-
"""rete_bayesiana-12.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ZGPl6wwryzQJjYd0tEYsx3h-1STj847b
"""

# bayesian network

"""1. Loading Libraries and Data"""

!pip install category_encoders
!pip install pandas
!pip install category-encoders
!pip install pgmpy
!pip install matplotlib
!pip install networkx
!pip install seaborn

import pandas as pd
import category_encoders as ce
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator, HillClimbSearch, BicScore, K2Score
from pgmpy.inference import VariableElimination
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns

df=pd.read_csv('/content/Amazon Customer Behavior Survey.csv')

"""2. Brief data analysis"""

df.head()

df.nunique()

df.drop('Timestamp', axis=1, inplace=True)

df.count()

df.info()

"""3. Data Pre-processing and visualization"""

cat_cols=df.select_dtypes(include=['object']).columns.tolist()
num_cols=df.select_dtypes(include=['int']).columns.tolist()

print(cat_cols)
print(num_cols)

for col in cat_cols[1:]:
    category_counts = df[col].value_counts()
    plt.figure(figsize=(15, 4))
    category_counts.plot(kind='bar')
    plt.title(col)
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

for col in num_cols:
    category_counts = df[col].value_counts()
    plt.figure(figsize=(15, 4))
    category_counts.plot(kind='bar')
    plt.title(col)
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

import category_encoders as ce

nominal_cols = ['Gender', 'Purchase_Categories', 'Search_Result_Exploration','Cart_Abandonment_Factors', 'Service_Appreciation', 'Improvement_Areas', 'Product_Search_Method', 'Add_to_Cart_Browsing' ]
ordinal_encoder = ce.OrdinalEncoder(cols=nominal_cols)
df[nominal_cols] = ordinal_encoder.fit_transform(df[nominal_cols])

ordinal_encoder = ce.OrdinalEncoder(cols=['Purchase_Frequency', 'Browsing_Frequency', 'Saveforlater_Frequency', 'Review_Reliability'])
df = ordinal_encoder.fit_transform(df)

df.head()

binary_col = ['Review_Left']
binary_mapping = {'Yes': 1, 'No': 0}

for col in binary_col:
    if col in df.columns:
        df[col] = df[col].map(binary_mapping).fillna(df[col])
    else:
        print(f"{col} is not in the DataFrame")

tri_cols = ['Personalized_Recommendation_Frequency', 'Recommendation_Helpfulness', 'Review_Helpfulness']
trinary_mapping = {'Yes': 1, 'No': 0, 'Sometimes':2}
for col in tri_cols:
    if col in df.columns:
        df[col] = df[col].map(trinary_mapping)
    else:
        print(f"{col} is not in the DataFrame")

df.head()

df.describe()

"""4. Defining the nodes and the structure"""

# Define nodes
nodes = list(df.columns)

# empty graph
G = nx.DiGraph()
G.add_nodes_from(nodes)
plt.figure(figsize=(10, 8))
nx.draw(G, with_labels=True, node_size=3000, node_color='skyblue', font_size=15, font_weight='bold')
plt.show()

"""5. Using hillclimb search to find the structures"""

from pgmpy.estimators import HillClimbSearch, BicScore, BDeuScore, K2Score # BDeuScore is case sensitive

# Hill Climb Search with different scoring methods
hc = HillClimbSearch(df)
bic_model = hc.estimate(scoring_method=BicScore(df))
bdeu_model = hc.estimate(scoring_method=BDeuScore(df))
k2_model = hc.estimate(scoring_method=K2Score(df))

# Calculate and print the scores
bic_score = BicScore(df).score(bic_model)
bdeu_score = BDeuScore(df).score(bdeu_model)
k2_score = K2Score(df).score(k2_model)

print(f"BIC Score: {bic_score}")
print(f"BDeu Score: {bdeu_score}")
print(f"K2 Score: {k2_score}")

#  nodes and edges
print("Nodes in k2 model:", k2_model.nodes())
print("Edges in k2 model:", k2_model.edges())


if k2_model.nodes() and k2_model.edges():
    # show network
    pos = nx.circular_layout(k2_model)
    plt.figure(figsize=(15, 12))
    nx.draw(k2_model, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=8, font_weight='bold', arrows=True)
    plt.title("K2 Model Structure (Circular Layout)")
    plt.show()
else:
    print("The k2 model has no nodes or edges to visualize.")

#  nodes and edges
print("Nodes in BIC model:", bic_model.nodes())
print("Edges in BIC model:", bic_model.edges())


if bic_model.nodes() and bic_model.edges():
    # show network
    pos = nx.circular_layout(bic_model)
    plt.figure(figsize=(15, 12))
    nx.draw(bic_model, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=8, font_weight='bold', arrows=True)
    plt.title("BIC Model Structure (Circular Layout)")
    plt.show()
else:
    print("The bic model has no nodes or edges to visualize.")

"""looks like the BDeuScore is the best since it is less negative. we will denote the bdeu_model as the best_model from now on."""

# Select the best model based on scoring
best_model_structure = bic_model if BicScore(df).score(bic_model) > BDeuScore(df).score(bdeu_model) else bdeu_model
best_model = BayesianNetwork(best_model_structure.edges())
best_model.fit(df, estimator=MaximumLikelihoodEstimator)

#  nodes and edges
print("Nodes in best model:", best_model.nodes())
print("Edges in best model:", best_model.edges())


if best_model.nodes() and best_model.edges():
    # show network
    pos = nx.circular_layout(best_model)
    plt.figure(figsize=(15, 12))
    nx.draw(best_model, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=8, font_weight='bold', arrows=True)
    plt.title("Best Model Structure (Circular Layout)")
    plt.show()
else:
    print("The best model has no nodes or edges to visualize.")

"""6. Performing inference on the best model"""

# inference
inference = VariableElimination(best_model)
result = inference.query(variables=['Purchase_Frequency'], evidence={'Gender': 1})

# function to plot CPTs
def plot_cpt(discrete_factor, title):
    state_names = list(discrete_factor.state_names.values())
    if len(state_names) > 1:
        state_combinations = pd.MultiIndex.from_product(state_names, names=discrete_factor.state_names.keys())
        values = discrete_factor.values.flatten()
        cpt_df = pd.DataFrame(values.reshape(len(state_names[0]), len(state_names[1])), index=state_names[0], columns=state_names[1])
    else:
        values = discrete_factor.values
        cpt_df = pd.DataFrame(values, index=state_names[0], columns=[title])
    plt.figure(figsize=(10, 6))
    sns.heatmap(cpt_df, annot=True, cmap='viridis', cbar=True)
    plt.title(f'Conditional Probability Table for {title}')
    plt.xlabel('States')
    plt.ylabel('Probability')
    plt.show()

# result of the inference
plot_cpt(result, 'Purchase_Frequency')

#  marginal probabilities
marginal_prob_purchase_frequency = inference.query(variables=['Purchase_Frequency'])
print("Marginal probability of Purchase_Frequency:\n", marginal_prob_purchase_frequency)

marginal_prob_browsing_frequency = inference.query(variables=['Browsing_Frequency'])
print("Marginal probability of Browsing_Frequency:\n", marginal_prob_browsing_frequency)

marginal_prob_add_to_cart_browsing = inference.query(variables=['Add_to_Cart_Browsing'])
print("Marginal probability of Add_to_Cart_Browsing:\n", marginal_prob_add_to_cart_browsing)

"""7. Estimation for the best model"""

# Maximum Likelihood Estimation
best_model.fit(df, estimator=MaximumLikelihoodEstimator)

"""8. Independcies, chi-sq"""

from pgmpy.independencies import Independencies

# local independencies of 'Purchase_Frequency'
local_independencies = best_model.local_independencies('Purchase_Frequency')
print("Local independencies for Purchase_Frequency:\n", local_independencies)

from scipy.stats import chi2_contingency

def test_direct_dependency(data, var1, var2):
    contingency_table = pd.crosstab(data[var1], data[var2])
    chi2, p, dof, ex = chi2_contingency(contingency_table)
    return p, chi2, dof

# Example nodes to test direct dependencies
dependencies_to_test = [
    ('Purchase_Frequency', 'Personalized_Recommendation_Frequency'),
    ('Personalized_Recommendation_Frequency', 'Recommendation_Helpfulness'),
    ('Recommendation_Helpfulness', 'Purchase_Frequency')
]

# Perform the tests and print results
for var1, var2 in dependencies_to_test:
    p_value, chi2_stat, dof = test_direct_dependency(df, var1, var2)
    print(f"Direct dependency test between {var1} and {var2}:")
    print(f"p-value: {p_value}, chi2_stat: {chi2_stat}, degrees of freedom: {dof}\n")

"""9. BIC and AIC scores of best model"""

bic_score = BicScore(df).score(best_model)
print(f"BIC Score: {bic_score}")

from pgmpy.estimators import AICScore
aic = AICScore(df)
aic_score = aic.score(best_model)
print(f"AIC Score of the best model: {aic_score}")

"""10. Specific Queries"""

# Perform inference on the best model with specific evidence
evidence = {'Purchase_Frequency': 3}
results = {}
for variable in best_model.nodes():
    if variable not in evidence:
        query_result = inference.query(variables=[variable], evidence=evidence)
        results[variable] = query_result
        print(f"Query for {variable} given {evidence}:")
        print(query_result)
        print("\n")


evidence = {'Purchase_Frequency': 1, 'Gender': 2}
result = inference.query(variables=['Saveforlater_Frequency'], evidence=evidence)
print(result)

node1 = 'Purchase_Frequency'
node2 = 'Browsing_Frequency'
contingency_table = pd.crosstab(df[node1], df[node2])
chi2, p, dof, ex = chi2_contingency(contingency_table)
print(f"Chi-Squared Test: {chi2}, p-value: {p}, degrees of freedom: {dof}")

contingency_table = pd.crosstab(df['Purchase_Frequency'], df['Browsing_Frequency'])
print(contingency_table)

"""11. Optimizing the best model to obtain the final model"""

c = HillClimbSearch(df)
best_model_structure_opt = hc.estimate(scoring_method=BicScore(df))
best_model_opt = BayesianNetwork(best_model_structure_opt.edges())
best_model_opt.fit(df, estimator=MaximumLikelihoodEstimator)
print(f"BIC Score of the optimized model: {BicScore(df).score(best_model_opt)}")

"""This BIC score is less negative than the initial BIC score of the best_model. So the first best_model is the final model."""