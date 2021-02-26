## DyEgoVis
An interactive visualization system that allows users to explore the evolutions of dynamic ego-networks at the three analysis levels: global level, local level and individual level. 

Demo video: http://jalamao.top/file/DyEgoVis.mp4

## Installation Steps
The visualization system can run in Ubuntu or Windows system. It consists of server and frontend.

### Server
1. To install the dependency packages of the system server, under the project dir "server", open the terminal and run the command:
    ```
      pip install -r requirements.txt
    ```
2. Install MongDB (a document-oriented database management system) in your computer.

3. Import the json files in the project dirs "MongDB/enron" and "MongDB/tvcg" into your MongDB according to the scheme shown in the picture "MongoDB/Directory_of_DB_collections.png".

4. Run the file "App.py".

### Frontend
1. Install Node.js in your computer.

2. To install the dependency packages of the frontend, under the project dir "frontend", open the terminal and run the command:
   ```
    npm install
   ```
3. Under the project dir "frontend", open the terminal and run the command:
   ```
    sudo npm run dev
   ```
4. Access the system interface at http://localhost:8080 in your browser.
