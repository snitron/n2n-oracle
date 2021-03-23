pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

interface ValidatorsManagement {

    function getValidators() external returns (address[] memory);
    
    function getThreshold() external view returns (uint256);
}

contract Bridge {

    struct Transaction {
        bytes32 id;
        address[] acceptors;
        address payable recipient;
        uint256 amount;
    }

    modifier isAdmin {
        require(msg.sender == administator, "Prohibited.");
        _;
    }
    
    modifier isValidator {
        validators = ValidatorsManagement(validatorsManager).getValidators();
        
        require(isSenderValidator(msg.sender), "Prohibited.");
        _;
    }
    
    address administator;
    address validatorsManager;
    address[] validators;
    
    uint256 own_liquidity;
    uint256 opposite_liquidity;
    uint256 l;

    bool is_left;

    Transaction[] transactions;
    
    event bridgeActionInitiated(address recipient, uint256 amount);

    constructor(address _validatorsManager, bool _is_left) public {
        validatorsManager = _validatorsManager;
        administator = msg.sender;
        is_left = _is_left;
    }
    
    function changeValidatorSet(address newvalidatorset) public isAdmin {
        validatorsManager = newvalidatorset;
    }
    
    function addLiquidity() public payable isAdmin {
        require (msg.value != 0, "Invalid tokenss count.");
        require (!is_left, "Only right side allowed");

        own_liquidity += msg.value;
    }
    
    function isSenderValidator(address validator) private view returns (bool) {
        for (uint256 i = 0; i < validators.length; i++) {
            if (validators[i] == validator) {
                return true;
            }
        }
        
        return false;
    }
    
    function updateLiquidityLimit(uint256 newlimit) external isAdmin {
        require (msg.sender == administator, "Prohibited.");
        require (is_left, "Only left side allowed");
        
        own_liquidity = newlimit;
        l = newlimit;
    }
    
    function getLiquidityLimit() public view returns (uint256) {
        if (is_left) {
            return l;
        } else {
            return address(this).balance;
        }
    }
    
    function commit(address payable recipient, uint256 amount, bytes32 id) external isValidator {
        require (amount <= address(this).balance, "Too small liquidity.");
        
        address sender = msg.sender;
        bool is_operation_exist = false;
        uint256 oper_id;
        uint256 acceptors_count = 0;
        
        for (uint256 i = 0; i < transactions.length; i++) {
            if (transactions[i].recipient == recipient && transactions[i].amount == amount && transactions[i].id == id) { //!
                oper_id = i;
                
                is_operation_exist = true;
                bool is_checlk_norm = true;
                
                for (uint256 j = 0; j < transactions[i].acceptors.length; j++) {
                    is_checlk_norm = is_checlk_norm && (transactions[i].acceptors[j] != sender);
                }
                
                require (is_checlk_norm, "Already commited.");
                
                transactions[i].acceptors.push(sender);
                acceptors_count = transactions[i].acceptors.length;
            }
        }
        
        if (!is_operation_exist) {
            address[] memory a;
         
            Transaction memory newTransaction = Transaction(id, a, recipient, amount);

            transactions.push(newTransaction);
            oper_id = transactions.length - 1;
            
            transactions[oper_id].acceptors.push(sender);
            acceptors_count = 1;
        }
        
        if (acceptors_count >= ValidatorsManagement(validatorsManager).getThreshold()) {
            recipient.transfer(amount);
            
            opposite_liquidity += amount;
            own_liquidity -= amount;
            l += amount;
            
            transactions[oper_id] = transactions[transactions.length - 1];
            transactions.pop();
        }
    }
 
    receive() payable external {
        require (msg.value != 0, "Incorrect amount.");
        require (msg.value <= l, "Too small liquidity.");

        own_liquidity += msg.value;
        opposite_liquidity -= msg.value;
        l -= msg.value;

        emit bridgeActionInitiated(msg.sender, msg.value);
    }
}
