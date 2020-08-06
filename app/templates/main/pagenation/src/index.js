/** @format */

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { Pagination } from 'semantic-ui-react';

const INJECT_DIV_TAG = 'result-list-target';
const PAGE_SIZE_NAME = 'page_size';
const container = document.getElementById(INJECT_DIV_TAG);

const ResultCard = ({ entry }) => {
  function isExpired(end_date) {
    const parts = end_date.split('-');
    const end_date_converted = new Date(parts[0], parts[1] - 1, parts[2]);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return end_date_converted >= today ? 'Active' : 'Expired';
  }
  return (
    <div key={entry.original_contract_id}>
      <div class="paper">
        <div class="ui grid">
          <div class="eight wide column">
            <h3 class="theme-primary">{entry.vendor}</h3>
            <p>
              <b>ID:</b> {entry.original_contract_id} &nbsp; • &nbsp;
              <b>As Of:</b> {entry.as_of}
            </p>
          </div>
          <div class="eight wide column">
            <div style={{ lineHeight: '20px' }}>
              <div class="tag">STAT</div>
              <b>{isExpired(entry.end_dt)}</b>
            </div>
            <div style={{ lineHeight: '20px' }}>
              <div class="tag">TYPE</div>
              <b>{entry.contract_structure_type}</b>
            </div>
            <div style={{ lineHeight: '20px' }}>
              <div class="tag">DEPT</div>
              <b>
                {entry.department_name.replace(/\w\S*/g, function (txt) {
                  return (
                    txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
                  );
                })}
              </b>
            </div>
            <div style={{ lineHeight: '20px' }}>
              {entry.amt == 0 ? (
                <div>
                  <div class="tag">PAID</div>
                  <b> 100.00%</b>
                </div>
              ) : (
                <div>
                  <div class="tag">PAID</div>
                  <b>{Math.round((100 * entry.tot_payments) / entry.amt)}%</b>
                </div>
              )}
            </div>
          </div>
        </div>
        <div class="ui grid">
          <div class="eight wide column">
            <p>
              <b>Total Payments:</b> $
              {Number(entry.tot_payments).toLocaleString()}
            </p>
            <p>
              <b>Contract Amount:</b> ${Number(entry.amt).toLocaleString()}
            </p>
            <p
              style={{
                fontWeight: 600,
                textTransform: 'uppercase',
                color: '#0f4d90',
              }}
            >
              Profit Status: {entry.profit_status.replace(/_/g, ' ')}{' '}
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
                textTransform: 'uppercase',
                color: '#0f4d90',
              }}
            >
              Advertising Status: {entry.adv_or_exempt}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

class ResultListContainer extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      page_size: props.page_size,
      loading: false,
      start: 0,
      end: props.page_size,
      result_list: window.filtered_json.map((x) => {
        x.percentPaid = Math.round((100 * x.tot_payments) / x.amt);
        return x;
      }),
    };
  }

  handlePageChange(data) {
    const activePage = data.activePage,
      start = (activePage - 1) * 20,
      end = activePage * 20;

    console.log(`start: ${start}, end: ${end}`);
    this.setState({ start, end });
    window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
  }

  // amt desc
  sortByAmtDesc = () => {
    this.setState({ loading: true });
    console.log('sort by amount desc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return b.amt - a.amt;
      }),
    });
    this.setState({ loading: false });
  };

  // amt asc
  sortByAmtAsc = () => {
    this.setState({ loading: true });
    console.log('sort by amount asc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return a.amt - b.amt;
      }),
    });
    this.setState({ loading: false });
  };

  sortByVendorDesc = () => {
    this.setState({ loading: true });
    console.log('sort by vendor desc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        if (a.vendor < b.vendor) return 1;
        else if (a.vendor > b.vendor) return -1;
        return 0;
      }),
    });
    this.setState({ loading: false });
  };

  sortByVendorAsc = () => {
    this.setState({ loading: true });
    console.log('sort by vendor asc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        if (a.vendor > b.vendor) return 1;
        else if (a.vendor < b.vendor) return -1;
        return 0;
      }),
    });
    this.setState({ loading: false });
  };

  // latest to oldest
  sortByDateAsce = () => {
    this.setState({ loading: true });
    console.log('sort date by asce');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return a.end_dt > b.end_dt ? 1 : -1;
      }),
    });
    this.setState({ loading: false });
  };

  // latest to oldest
  sortByDateDesc = () => {
    this.setState({ loading: true });
    console.log('sort date by desc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return b.end_dt > a.end_dt ? 1 : -1;
      }),
    });
    this.setState({ loading: false });
  };

  // smallest to largest
  sortByPaidAsc = () => {
    this.setState({ loading: true });
    console.log('sort paid by asce');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return a.percentPaid - b.percentPaid;
      }),
    });
    this.setState({ loading: false });
  };

  // largest to smallest
  sortByPaidDesc = () => {
    this.setState({ loading: true });

    console.log('sort paid by desc');
    this.setState({
      result_list: this.state.result_list.sort((a, b) => {
        return b.percentPaid - a.percentPaid;
      }),
    });
    this.setState({ loading: false });
  };

  render() {
    const loadingStatus = this.state.loading;
    const subResult = this.state.result_list.slice(
      this.state.start,
      this.state.end
    );
    const totalPages = Math.ceil(
      this.state.result_list.length / this.state.page_size
    );

    return (
      <div>
        {!loadingStatus && (
          <>
            {subResult.map((val) => (
              <ResultCard entry={val} />
            ))}
          </>
        )}
        <div style={{ marginTop: '50px', height: '30vh', float: 'right' }}>
          <Pagination
            defaultActivePage={1}
            totalPages={totalPages}
            onPageChange={(event, data) => this.handlePageChange(data)}
          />
        </div>
      </div>
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
