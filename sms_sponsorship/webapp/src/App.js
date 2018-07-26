import React from 'react';
import TopAppBar from './components/TopAppBar';
import ChildCard from './components/ChildCard';
import CircularProgress from '@material-ui/core/CircularProgress';
import Typography from '@material-ui/core/Typography';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import CenteredLoading from './components/CenteredLoading';
import jsonRPC from './components/jsonRPC';
import getRequestId from './components/getRequestId';
import Message from './components/Message';

const theme = createMuiTheme({
    palette: {
        primary: {
            main: '#0054A6'
        },
    },
});

window.pageLoaded = false;
window.getChildTimeout = false;

class Main extends React.Component {
    state = {
        child: false,
        partner: false,
        success: false,
    };

    parseResult = (res) => {
        let child;
        try {
            child = JSON.parse(res.responseText).result[0]
        }
        catch(e) {
            child = false;
        }
        return child;
    };

    getChild = () => {
        let requestId = getRequestId();
        if (!requestId) {
            return;
        }
        let url = "/sms_sponsorship/step1/" + requestId + "/get_child_data";
        jsonRPC(url, {}, (res) => {
            let child = this.parseResult(res);
            let partner = (typeof(child.partner) === 'undefined') ? false:child.partner[0];
            this.setState({
                child: child,
                partner: partner,
            });
        });
    };

    changeChild = () => {
        let requestId = getRequestId();
        let url = "/sms_sponsorship/step1/" + requestId + "/change_child";
        let form = document.forms.other_child_form;

        let data = {
            gender: form.gender.value,
            age: form.age.value,
            country: form.country.value,
        };

        this.setState({
            child: {
                'has_a_child': true,
                'loading_other_child': true
            }
        });

        jsonRPC(url, data, (res) => {
            this.getChild();
        });
    };

    componentDidMount() {
        if (!window.pageLoaded) {
            window.pageLoaded = true;
            this.getChild();
        }
    }

    render() {
        let child = this.state.child;
        let topAppBar = <TopAppBar title="Compassion"/>;

        if (!getRequestId()) {
            return (
                <div>
                    {topAppBar}
                    <div>
                        <Message text="Error : no SMS request ID. Please send an other SMS."/>
                    </div>
                </div>
            )
        }

        if (!child.has_a_child) {
            clearTimeout(window.getChildTimeout);
            window.getChildTimeout = setTimeout(() => {
                this.getChild();
            }, 1000);
        }

        return (
            <div>
                {topAppBar}
                {this.state.success ? (
                    <div>
                        <Message text="Thank you for your sponsorship !"/>
                    </div>
                    ):(
                    <div>
                        {child ? (
                            <div>
                                {child.sponsorship_confirmed ? (
                                    <div>
                                        <Message text="You already sponsored this child, thank you ! <br/><br/>
                                        If you want to sponsor an other child, please send another SMS."/>
                                    </div>
                                ):(
                                    <div>
                                        {!child.invalid_sms_child_request ? (
                                            <div>
                                                {!child.loading_other_child ? (
                                                    <div>
                                                        {child.has_a_child ? (
                                                            <ChildCard centered
                                                                       name={child.name}
                                                                       country={child.field_office_id[1]}
                                                                       age={child.age + ' years'}
                                                                       gender={child.gender === 'M' ? 'Male':'Female'}
                                                                       image_url={child.image_url}
                                                                       appContext={this}/>
                                                        ):(
                                                            <CenteredLoading text="no child reserved, please wait a few seconds"/>
                                                        )}
                                                    </div>
                                                ):(
                                                    <div>
                                                        <CenteredLoading text="searching a new child, please wait a few seconds"/>
                                                    </div>
                                                )}
                                            </div>
                                        ):(
                                            <div>
                                                <Message text="Error : child request invalid"/>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ):(
                            <div>
                                <CenteredLoading text="loading..."/>
                            </div>
                        )}
                    </div>
                )}
            </div>
        )
    }
}

export default () => {
    return (
        <MuiThemeProvider theme={theme}>
            <Main/>
        </MuiThemeProvider>
    );
}