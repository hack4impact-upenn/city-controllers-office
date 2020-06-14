import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

const INJECT_DIV_TAG = "result-list-target";
const container = document.getElementById(INJECT_DIV_TAG);

const ResultList = () => {
  useEffect(() => {
    console.log(window.filtered_json);
  }, []);
  return (
    <div>
      <h1>Hello World!</h1>
    </div>
  );
};

class ResultListContainer extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return <ResultList />;
  }
}

ReactDOM.render(<ResultListContainer />, container);
