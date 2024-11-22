import logging
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from pandas import DataFrame
from pandas.api.types import is_integer_dtype
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from freqtrade.freqai.base_models.BaseClassifierModel import BaseClassifierModel
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen


logger = logging.getLogger(__name__)


class XGBoostClassifier(BaseClassifierModel):
    """
    User created prediction model. The class inherits IFreqaiModel, which
    means it has full access to all Frequency AI functionality. Typically,
    users would use this to override the common `fit()`, `train()`, or
    `predict()` methods to add their custom data handling tools or change
    various aspects of the training that cannot be configured via the
    top level config.json file.
    """

    def fit(self, data_dictionary: dict, dk: FreqaiDataKitchen, **kwargs) -> Any:
        """
        User sets up the training and test data to fit their desired model here
        :param data_dictionary: the dictionary holding all data for train, test,
            labels, weights
        :param dk: The datakitchen object for the current coin/model
        """

        X = data_dictionary["train_features"].to_numpy()
        y = data_dictionary["train_labels"].to_numpy()[:, 0]

        le = LabelEncoder()
        if not is_integer_dtype(y):
            y = pd.Series(le.fit_transform(y), dtype="int64")

        if self.freqai_info.get("data_split_parameters", {}).get("test_size", 0.1) == 0:
            eval_set = None
        else:
            test_features = data_dictionary["test_features"].to_numpy()
            test_labels = data_dictionary["test_labels"].to_numpy()[:, 0]
            
            if not is_integer_dtype(test_labels):
                test_labels = pd.Series(le.transform(test_labels), dtype="int64")

            eval_set = [(X, y), (test_features, test_labels)]
            # eval_set = [(test_features, test_labels), (X, y)]

        train_weights = data_dictionary["train_weights"]

        init_model = self.get_init_model(dk.pair)

        from sklearn.model_selection import GridSearchCV
        param_grid = {
            "max_depth": [3, 5, 7],                 # Maximum depth of the trees
            "learning_rate": [0.01, 0.1, 0.2],     # Learning rate
            "n_estimators": [50, 100, 200],        # Number of boosting rounds
            "subsample": [0.6, 0.8, 1.0],          # Fraction of samples used per tree
            "colsample_bytree": [0.6, 0.8, 1.0],   # Fraction of features used per tree
            "reg_alpha": [0, 0.1, 1.0],            # L1 regularization term
            "reg_lambda": [0.1, 1.0, 10.0],        # L2 regularization term
        }

        base_model = XGBClassifier(
            objective="binary:logistic",  # For binary classification
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42
        )

        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            scoring="accuracy",  # Optimize for accuracy
            cv=3,  # 3-fold cross-validation
            verbose=1,
            n_jobs=-1  # Use all available CPU cores
        )
        
        # Perform grid search
        print("Starting Grid Search...")
        grid_search.fit(X, y, sample_weight=train_weights)
        print(f"Best parameters found: {grid_search.best_params_}")
        print(f"Best cross-validated score: {grid_search.best_score_}")

        # model = XGBClassifier(**self.model_training_parameters)
        model = XGBClassifier(
                    objective="binary:logistic",  # For binary classification problems
                    max_depth=5,                 # Maximum depth of the trees
                    learning_rate=0.1,           # Step size shrinkage
                    n_estimators=100,            # Number of boosting rounds
                    subsample=0.8,               # Fraction of training data used per tree
                    colsample_bytree=0.8,        # Fraction of features used per tree
                    reg_alpha=1.0,               # L1 regularization term
                    reg_lambda=1.0,              # L2 regularization term
                    random_state=42,             # Seed for reproducibility
                    eval_metric="logloss",       # Metric to evaluate during training
                    use_label_encoder=False      # Disables internal label encoding (avoids warnings)
                )

        from freqtrade.freqai.tensorboard import TBCallback
        from pathlib import Path
        
        model.set_params(callbacks=[TBCallback(Path(dk.data_path).parent)])
        model.set_params(eval_metric=["map", "logloss", 'error', 'auc'])
        model.fit(X=X, y=y, eval_set=eval_set, sample_weight=train_weights, xgb_model=init_model)

        return model

    def predict(
        self, unfiltered_df: DataFrame, dk: FreqaiDataKitchen, **kwargs
    ) -> tuple[DataFrame, npt.NDArray[np.int_]]:
        """
        Filter the prediction features data and predict with it.
        :param unfiltered_df: Full dataframe for the current backtest period.
        :return:
        :pred_df: dataframe containing the predictions
        :do_predict: np.array of 1s and 0s to indicate places where freqai needed to remove
        data (NaNs) or felt uncertain about data (PCA and DI index)
        """

        (pred_df, dk.do_predict) = super().predict(unfiltered_df, dk, **kwargs)

        le = LabelEncoder()
        label = dk.label_list[0]
        labels_before = list(dk.data["labels_std"].keys())
        labels_after = le.fit_transform(labels_before).tolist()
        pred_df[label] = le.inverse_transform(pred_df[label])
        pred_df = pred_df.rename(
            columns={labels_after[i]: labels_before[i] for i in range(len(labels_before))}
        )

        return (pred_df, dk.do_predict)






