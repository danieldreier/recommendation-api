import {Construct} from 'constructs';
import {App, RemoteBackend, TerraformStack} from 'cdktf';
import {AwsProvider} from '../.gen/providers/aws';
import {config} from './config';
import {DynamoDB} from "./dynamodb";

class ExploreTopics extends TerraformStack {
    constructor(scope: Construct, name: string) {
        super(scope, name);

        new AwsProvider(this, 'aws', {
            region: 'us-east-1',
        });

        new RemoteBackend(this, {
            hostname: 'app.terraform.io',
            organization: 'Pocket',
            workspaces: [
                {
                    prefix: `${config.name}-`,
                },
            ],
        });

        new DynamoDB(scope, 'dynamodb');
    }
}

const app = new App();
new ExploreTopics(app, 'explore-topics');
app.synth();
