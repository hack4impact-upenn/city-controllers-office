import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import { Pagination } from "semantic-ui-react";

const INJECT_DIV_TAG = "result-list-target";
const PAGE_SIZE_NAME = "page_size";
const container = document.getElementById(INJECT_DIV_TAG);

const ResultList = ({
  page_size: page_size_prop,
  result_list: result_list_prop,
}) => {
  const result_list = result_list_prop;
  const page_size = page_size_prop;
  const totalPages = Math.ceil(result_list.length / page_size);
  const [page, setPage] = useState({ start: 0, end: page_size });

  function handlePageChange(data) {
    const activePage = data.activePage,
      start = (activePage - 1) * page_size,
      end = activePage * page_size;

    setPage({ start: start, end: end });
    // window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    window.scrollTo({ top: 0, left: 0 });
  }

  function EntryList() {
    return (
      <div>
        {result_list.slice(page.start, page.end).map((entry) => {
          return (
            <div key={entry.original_contract_id}>
              <div class="paper">
                <div class="ui grid">
                  <div class="eight wide column">
                    <h3 class="theme-primary">{entry.vendor}</h3>
                    <p>
                      <i>ID: {entry.original_contract_id}</i>
                    </p>
                  </div>
                  <div class="eight wide column">
                    <div style={{ lineHeight: "20px" }}>
                      <div class="tag">TYPE</div>
                      <b>{entry.contract_structure_type}</b>
                    </div>
                    <div style={{ lineHeight: "20px" }}>
                      <div class="tag">DEPT</div>
                      <b>{entry.department_name}</b>
                    </div>
                    <div style={{ lineHeight: "20px" }}>
                      {entry.amt == 0 ? (
                        <div>
                          <div class="tag">PAID</div>
                          <b> 100.00%</b>
                        </div>
                      ) : (
                        <div>
                          <div class="tag">PAID</div>
                          <b>{entry.percentPaid}%</b>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div class="eight wide column">
                  <p>
                    <b>Total Payments:</b> {entry.tot_payments}
                  </p>
                  <p>
                    <b>Contact Amount:</b> {entry.amt}
                  </p>
                  <p
                    style={{
                      fontWeight: 600,
                      textTransform: "uppercase",
                      color: "#0f4d90",
                    }}
                  >
                    Profit Status: {entry.profit_status}{" "}
                  </p>
                </div>
                <div class="eight wide column">
                  <p>
                    <b>Description:</b> {entry.short_desc}
                  </p>
                  <p>
                    <b>Contract Term:</b> {entry.start_dt} to {entry.end_dt}
                  </p>
                  <p
                    style={{
                      fontWeight: 600,
                      textTransform: "uppercase",
                      color: "#0f4d90",
                    }}
                  >
                    Exempt Status: {entry.adv_or_exempt}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <>
      <EntryList />
      <div style={{ marginTop: "50px", height: "30vh" }}>
        <Pagination
          defaultActivePage={1}
          totalPages={totalPages}
          onPageChange={(_, data) => handlePageChange(data)}
        />
      </div>
    </>
  );
};

class ResultListContainer extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      page_size: props.page_size,
      result_list: window.filtered_json.map((x) => {
        x.percentPaid = Math.round((100 * x.tot_payments) / x.amt);
        return x;
      }),
    };
  }

  // latest to oldest
  sortByDateAsce = () => {
    console.log("sort date by asce");

    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return a.end_dt > b.end_dt ? 1 : -1;
      }),
    });
  };

  // latest to oldest
  sortByDateDesc = () => {
    console.log("sort date by desc");
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return b.end_dt > a.end_dt ? 1 : -1;
      }),
    });
  };

  // smallest to largest
  sortByPaidAsc = () => {
    console.log("sort paid by asce");

    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return a.percentPaid - b.percentPaid;
      }),
    });
  };

  // largest to smallest
  sortByPaidDesc = () => {
    console.log("sort paid by desc");
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return b.percentPaid - a.percentPaid;
      }),
    });
  };

  render() {
    return (
      <ResultList
        page_size={this.state.page_size}
        result_list={this.state.result_list}
      />
    );
  }
}

ReactDOM.render(
  <ResultListContainer
    page_size={document
      .getElementById(INJECT_DIV_TAG)
      .getAttribute(PAGE_SIZE_NAME)}
    ref={(resultList) => (window.resultList = resultList)}
  />,
  container
);
