# Market Basket Analysis - Association Rules🥼👖🕶👟🩴👘
### ☝🏻☝🏻Sale  boosting is much easier, when you know purchasing behaviors. 😇😇😇

![Market Basket Analysis](https://user-images.githubusercontent.com/50080574/223110305-866880d6-0e96-4668-ab9c-8aafe2326119.jpg)



Sale boosting☝🏻, one of the most popular and common thing almost every company would like to adopt. One of the popular way to do so, is to deploy "Market Basket Analysis" or "Association Rules" which might provides customerss purchasing behaviors, what item or itemset they usually purchase. What items they alway buy together.

### Therefore, as a company, we can use these pattern to develop appropriated strategies to boost the sale and get more profit.


### These files show you the raw data (From ChulaMooc), the code, and result from the model which might be easy for you to get some ideas. I also appreciate for any feedback and comment which might be helpful to improve my skills. 😍

### Credit:
 1. Thank for raw data from Data Master program. ❤️
 2. Thank ChulaMooc for dataset.❤️
 3. Thank A. Ada for the new way to find missing value. ❤️
 4. Thank for the libraries I used. ❤️

### 👌👌👌Note: This project is allowed only private and non-commercial used only.👌👌👌

### Please enjoy my project😁

# This is the process of this project
![Slide2](https://user-images.githubusercontent.com/50080574/223110650-ddb6bf56-0f20-4a4b-96f4-7525a0bd1db1.PNG)


#### Step 1) Data Reading & Exploration
After I imported libraries which are used in this project, I read dataset, select only the columns I need, and explore.
With the easy medthod from A. Ada, I can easily find there is some missing value.

![image](https://user-images.githubusercontent.com/50080574/223111806-7ad06e74-51dc-4d61-bfde-5a206780960e.png)

![image](https://user-images.githubusercontent.com/50080574/223111982-17f8e2ff-6b57-458e-8b4d-72ac901082c1.png)

![image](https://user-images.githubusercontent.com/50080574/223112055-8f79058c-2451-4596-a45c-022db6614f18.png)

Luckily, number of missing value is acceptable if I remove them.

#### Step 2) Data Cleaning & Preparation
I droped rows contain missing value, also the rows where 'StockCode" DID NOT start with digit (number)
because the stock codes start from A-Z are not represent products, they present other activities.

![image](https://user-images.githubusercontent.com/50080574/223113092-81c0faaf-47a0-44a1-8ec5-51c551092efd.png)

![image](https://user-images.githubusercontent.com/50080574/223113149-aad3db63-b63f-4c7e-b89d-ccc30b587820.png)

As we want to localize our strategies, we focus on each country and do analysis for United Kingdom" first.

![image](https://user-images.githubusercontent.com/50080574/223113556-1fd7b00f-8947-492d-a48f-3ad1d31a74ea.png)

Then, I convert dataframe into listed format which is suitable for modelling.

![image](https://user-images.githubusercontent.com/50080574/223113888-648130e1-933f-47e0-904c-f13c3617eeac.png)

#### Step 3) Modelling
This step is easy, only 1 cell code, thank you the libraries developer who make it very easy for me.

![image](https://user-images.githubusercontent.com/50080574/223114351-610e96b8-406b-43b2-b4d5-f863c61886f3.png)

#### Step 4) DetaFrame Decoration
After I get the result, I put them in dataframe, where contains
 1. Antecedents
 2. Consequences
 3. Support
 4. Confidence
 5. Lift
 6. Conviction
to make it easy to understand.

![image](https://user-images.githubusercontent.com/50080574/223115199-8a300d8a-0727-4e9b-abbc-b502171ec783.png)

Decorate them to the format we want.

![image](https://user-images.githubusercontent.com/50080574/223115596-d730919a-25c5-4b89-8e42-1bd6aa8da75a.png)


#### Step 5) To CSV
The last step, save them into CSV file, don't for get to ignore index.

![image](https://user-images.githubusercontent.com/50080574/223115818-d009ddf2-9783-4eea-a822-e2d4d3a90c26.png)


### These are the example result of the project

When the customers purchase "RED HANGING HEART T-LIGHT HOLDER", there is 72% that they will also purchase "WHITE HANGING HEART T-LIGHT HOLDER"
![image](https://user-images.githubusercontent.com/50080574/223116365-6f8a64b3-e238-470b-a421-785c42f3a67e.png)

### Solution
1) Online: We can apply "You may also like" section to show the products the customers have high potential to purchase.
2) Offline: We can place the products the customers have high potential to buy together near each others for more convenient to them.

### Please enjoy my project😁
- [Market Basket Analysis - Association Rules: Sale boosting is much easier, when you know purchasingbehaviors](https://github.com/MariKoh/DataScienePortfolio/tree/master/Association%20Rules)
- [How To Use Data Analysis in Retail Industry](https://github.com/MariKoh/DataScienePortfolio/tree/master/How%20To%20Use%20Data%20Analysis%20in%20Retail%20Industry)
- [Fraud Detection in Insurance Industry](https://github.com/MariKoh/Business-and-Data-Analytics-Portfolio/tree/master/Fraud%20Data%20Analytics%20and%20Detection)
- [Customer Behavior in Insurance Industry](https://github.com/MariKoh/Business-and-Data-Analytics-Portfolio/tree/master/Insurance%20Customer%20Behavior)
