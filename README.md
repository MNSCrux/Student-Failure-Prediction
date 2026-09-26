# Student Performance Risk Dashboard

A machine learning project that predicts whether a university student is at risk of failing a course before the final exams.

The main idea behind the project was to use information about a student's performance during the semester to identify students who may need help early enough for something to actually be done about it.

This was my Final Year Project and I worked on the data collection, machine learning models, and dashboard.

## What the Project Does

The system takes student performance and academic information and uses a trained machine learning model to estimate the student's risk of failing.

The dashboard can then show things like:

* Student performance
* Predicted pass/fail risk
* Important performance information
* Recommendations based on the student's situation
* Student and teacher views

The goal was to make the prediction useful in a real academic setting rather than just training a model and looking at its accuracy.

## Project Phases

The project was divided into four main phases.

### Phase 1: Data Collection

I collected my own dataset instead of using an existing machine learning dataset.

The data was based around university student performance and included information that could potentially be available before final exams, such as academic performance and other student-related factors.

The dataset was then cleaned and prepared for use in the machine learning part of the project.

### Phase 2: Data Processing and Machine Learning

The collected data was processed using Python and prepared for model training.

I experimented with machine learning models and evaluated their performance on the student dataset.

The final model used for the dashboard was a Random Forest classifier.

Main technologies used:

* Python
* Pandas
* NumPy
* Scikit-learn
* Random Forest
* Jupyter Notebook

The model was trained to classify students based on their risk of failing.

### Phase 3: Risk Prediction

The trained model was integrated into the application so that student information could be passed through the model and converted into a risk prediction.

The important part of the system is that the prediction can be made before the final exams. This gives teachers or students an opportunity to identify problems while there is still time to improve performance.

The prediction is based on the information available to the system rather than the student's final result.

### Phase 4: Dashboard

The final phase was building the dashboard around the machine learning model.

The dashboard provides different views for students and teachers.

Students can see their own performance and risk information, while teachers can use the system to identify students who may need additional attention.

The dashboard also provides recommendations based on the student's performance.

## How It Works

The general workflow is:

```text
Student Data
     |
     v
Data Cleaning and Processing
     |
     v
Feature Preparation
     |
     v
Trained ML Model
     |
     v
Risk Prediction
     |
     v
Dashboard
     |
     +---- Student View
     |
     +---- Teacher View
```

A student's available academic information is passed to the trained model. The model produces a prediction that is then displayed through the dashboard.

## Machine Learning

The project uses a Random Forest classifier for the final prediction system.

The model was trained using the collected student dataset and evaluated during development before being integrated into the dashboard.

The purpose of the model is not to determine a student's final grade. It is meant to identify students who are showing patterns associated with a higher risk of failing so that the situation can be addressed before finals.

## Dashboard

The dashboard was designed around two main users.

### Student

The student view allows a student to see:

* Their academic performance
* Their predicted risk
* Relevant information about their current situation
* Recommendations for improving their performance

### Teacher

The teacher view allows teachers to look at student performance and identify students who may be at higher risk.

This makes the system more useful than having the prediction exist only inside a notebook or Python script.

## Technologies

### Machine Learning

* Python
* Pandas
* NumPy
* Scikit-learn
* Random Forest

### Dashboard

* Python
* Dash

### Development

* Jupyter Notebook
* Git
* GitHub

## Project Goals

The main goals of the project were:

1. Collect a student performance dataset.
2. Prepare and clean the collected data.
3. Train and evaluate machine learning models.
4. Build a model that can identify students at risk of failing.
5. Make predictions before the final exams.
6. Build a dashboard that makes the predictions understandable and useful.
7. Provide different functionality for students and teachers.

## Limitations

The predictions depend on the quality and amount of data available to the model.

A risk prediction is also not a guarantee that a student will pass or fail. Student performance can change after the prediction is made, especially when there is still time remaining in the semester.

The dataset was collected specifically for this project, so the results should not automatically be assumed to represent every university or student population.

## Project Status

This project was developed as my Final Year Project.

The main parts of the project include the data collection process, machine learning pipeline, trained model, and dashboard for displaying student risk predictions.
